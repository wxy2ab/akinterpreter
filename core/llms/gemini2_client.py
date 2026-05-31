import os
import json
import time
import base64
import httpx
from typing import Any, Dict, List, Union, Iterator
import google.generativeai as genai
from PIL import Image
import queue
import threading

from ratelimit import ratelimit, sleep_and_retry
from ..utils.log import logger as logging
from ..utils.handle_max_tokens import handle_max_tokens
from ..utils.config_setting import Config
from ._llm_api_client import LLMApiClient

class AsyncContentIterator(Iterator[str]):
    def __init__(self):
        self.queue = queue.Queue()
        self.is_done = False
        self.lock = threading.Lock()

    def add_content(self, content: str):
        self.queue.put(content)

    def mark_done(self):
        with self.lock:
            self.is_done = True
        self.queue.put(None)

    def __iter__(self):
        return self

    def __next__(self) -> str:
        item = self.queue.get()
        if item is None:
            raise StopIteration
        return item
    
class Gemini2Client(LLMApiClient ):
    def __init__(self,model :str = "gemini-2.0-flash-exp"):
        config = Config()
        api_key = config.get("google_api_key")
        if not api_key:
            raise ValueError("Google API key not found in configuration")

        self.model_name = model

        genai.configure(api_key=api_key)
        
        self.generation_config = {
            "temperature": 0.7,
            "top_p": 1,
            "top_k": 40,
            "max_output_tokens": 8192,
        }
        
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=self.generation_config
        )
        self.chat = self.model.start_chat()
        self.history = []
        self.stat = {"call_count": {"tool_chat": 0}, "total_tokens": 0}
        
    def _add_to_history(self, role: str, content: str):
        self.history.append({"role": role, "content": content})
        
    def _get_chat_history(self):
        return self.history

    def _create_stream_iterator(self, response) -> Iterator[str]:
        """Helper method to create a string iterator from a streaming response"""
        def generate():
            try:
                for chunk in response:
                    if hasattr(chunk, 'text') and chunk.text:
                        yield chunk.text
            except Exception as e:
                yield f"Error in stream: {str(e)}"
        
        return generate()

    #@sleep_and_retry
    #@ratelimit(max_calls=10, period=60)
    def one_chat(self, message: Union[str, List[Union[str, Any]]], is_stream: bool = False) -> Union[str, Iterator[str]]:
        """
        Execute a single chat interaction without using or storing chat history.
        
        Args:
            message: Either a string message or a list containing strings and other content (images, etc.)
            is_stream: Whether to stream the response
            
        Returns:
            Either a string response or an iterator of string chunks if streaming
        """
        try:
            # Create a new model instance for this single interaction
            temp_model = genai.GenerativeModel(
                model_name="gemini-2.0-flash-exp",
                generation_config=self.generation_config
            )
            
            # Handle different types of content
            if isinstance(message, str):
                if is_stream:
                    response = temp_model.generate_content(message, stream=True)
                    return self._create_stream_iterator(response)
                else:
                    response = temp_model.generate_content(message)
                    return response.text
            elif isinstance(message, list):
                # Process list of content (text, images, etc.)
                content_parts = []
                for part in message:
                    if isinstance(part, str):
                        content_parts.append(part)
                    elif isinstance(part, dict) and 'mime_type' in part and 'data' in part:
                        # Handle base64 encoded content
                        content_parts.append(part)
                    elif isinstance(part, Image.Image):
                        # Handle PIL Images
                        content_parts.append(part)
                    else:
                        logging.warning(f"Unsupported content type in message: {type(part)}")
                
                if is_stream:
                    response = temp_model.generate_content(content_parts, stream=True)
                    return self._create_stream_iterator(response)
                else:
                    response = temp_model.generate_content(content_parts)
                    return response.text
            else:
                raise ValueError(f"Unsupported message type: {type(message)}")
                
        except Exception as e:
            error_msg = f"Error in one_chat: {str(e)}"
            logging.error(error_msg)
            return error_msg if not is_stream else iter([error_msg])

    @handle_max_tokens
    def text_chat(self, message: str, is_stream: bool = False) -> Union[str, Iterator[str]]:
        self._add_to_history("user", message)
        
        if is_stream:
            return self._stream_response(message)
        else:
            response = self.chat.send_message(message)
            self._add_to_history("assistant", response.text)
            return response.text

    def image_chat(self, message: str, image_path: str) -> str:
        try:
            if image_path.startswith(('http://', 'https://')):
                # Handle URL-based images
                response = httpx.get(image_path)
                image_data = base64.b64encode(response.content).decode('utf-8')
                image_part = {'mime_type': 'image/jpeg', 'data': image_data}
            else:
                # Handle local image files
                image = Image.open(image_path)
                image_part = image
            
            self._add_to_history("user", f"{message} [Image: {image_path}]")
            response = self.model.generate_content([image_part, message])
            self._add_to_history("assistant", response.text)
            return response.text
            
        except Exception as e:
            error_msg = f"Error processing image chat: {str(e)}"
            logging.error(error_msg)
            return error_msg

    def multi_image_chat(self, message: str, image_paths: List[str]) -> str:
        try:
            content_parts = []
            for path in image_paths:
                if path.startswith(('http://', 'https://')):
                    response = httpx.get(path)
                    image_data = base64.b64encode(response.content).decode('utf-8')
                    content_parts.append({'mime_type': 'image/jpeg', 'data': image_data})
                else:
                    image = Image.open(path)
                    content_parts.append(image)
            
            content_parts.append(message)
            self._add_to_history("user", f"{message} [Images: {', '.join(image_paths)}]")
            response = self.model.generate_content(content_parts)
            self._add_to_history("assistant", response.text)
            return response.text
            
        except Exception as e:
            error_msg = f"Error processing multi-image chat: {str(e)}"
            logging.error(error_msg)
            return error_msg

    def tool_chat(self, user_message: str, tools: List[Dict[str, Any]], function_module: Any, is_stream: bool = False) -> Union[str, Iterator[str]]:
        """
        Note: The new Gemini API does not directly support function calling like the Vertex AI API.
        This method provides a basic implementation that parses the response for function calls.
        """
        self._add_to_history("user", user_message)
        
        # Prepare tools description for the model
        tools_description = "Available tools:\n" + "\n".join(
            f"- {tool['name']}: {tool['description']}" for tool in tools
        )
        
        prompt = f"{tools_description}\n\nUser message: {user_message}\n\nTo call a function, use the format: FUNCTION_CALL{{\"name\": \"function_name\", \"args\": {{\"arg1\": \"value1\"}}}}"
        
        if is_stream:
            return self._stream_tool_chat(prompt, tools, function_module)
        else:
            response = self.chat.send_message(prompt)
            return self._process_tool_response(response.text, tools, function_module)

    def _stream_tool_chat(self, prompt: str, tools: List[Dict[str, Any]], function_module: Any) -> Iterator[str]:
        iterator = AsyncContentIterator()
        threading.Thread(
            target=self._stream_tool_chat_thread,
            args=(prompt, tools, function_module, iterator)
        ).start()
        return iterator

    def _stream_tool_chat_thread(self, prompt: str, tools: List[Dict[str, Any]], function_module: Any, iterator: "AsyncContentIterator"):
        try:
            response = self.chat.send_message(prompt, stream=True)
            full_response = ""
            
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    iterator.add_content(chunk.text)
                    
            # Process any function calls in the complete response
            self._process_tool_response(full_response, tools, function_module, iterator)
            
        except Exception as e:
            error_msg = f"Error in tool chat stream: {str(e)}"
            logging.error(error_msg)
            iterator.add_content(f"\nError: {error_msg}")
        finally:
            iterator.mark_done()

    def _process_tool_response(self, response: str, tools: List[Dict[str, Any]], function_module: Any, iterator: AsyncContentIterator = None) -> str:
        try:
            # Look for function calls in the format FUNCTION_CALL{...}
            import re
            function_calls = re.finditer(r'FUNCTION_CALL({[^}]+})', response)
            
            for match in function_calls:
                try:
                    function_data = json.loads(match.group(1))
                    function_name = function_data.get('name')
                    function_args = function_data.get('args', {})
                    
                    result = self._execute_function(function_name, function_args, function_module)
                    
                    if iterator:
                        iterator.add_content(f"\nFunction result: {result}\n")
                    else:
                        response += f"\nFunction result: {result}\n"
                        
                except json.JSONDecodeError as e:
                    logging.error(f"Error parsing function call: {str(e)}")
                    
            return response
            
        except Exception as e:
            error_msg = f"Error processing tool response: {str(e)}"
            logging.error(error_msg)
            return error_msg

    def _execute_function(self, function_name: str, function_args: Dict[str, Any], function_module: Any) -> Any:
        try:
            if function_name == "CodeRunner":
                return self.CodeRunner(function_args.get("code", ""))
            elif hasattr(function_module, function_name):
                function = getattr(function_module, function_name)
                return function(**function_args)
            else:
                return f"Function {function_name} not found"
        except Exception as e:
            error_msg = f"Error executing function {function_name}: {str(e)}"
            logging.error(error_msg)
            return error_msg

    def tool_invoke(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        tools_description = "Available tools:\n" + "\n".join(
            f"- {tool.get('function', {}).get('name', tool.get('name', ''))}: "
            f"{tool.get('function', {}).get('description', tool.get('description', ''))}"
            for tool in tools
        )
        prompt = (
            f"{tools_description}\n\nConversation:\n{self._messages_to_prompt(messages)}\n\n"
            "If a tool is needed, respond with FUNCTION_CALL"
            "{\"name\": \"tool_name\", \"args\": {}}. You may also include normal text."
        )
        response = self.chat.send_message(prompt)
        text = getattr(response, "text", "") or ""

        import re
        tool_calls = []
        for index, match in enumerate(re.finditer(r"FUNCTION_CALL({.*?})", text, re.DOTALL)):
            try:
                function_data = json.loads(match.group(1))
            except json.JSONDecodeError:
                continue
            tool_calls.append({
                "id": str(index),
                "function": {
                    "name": function_data.get("name", ""),
                    "arguments": json.dumps(function_data.get("args", {}), ensure_ascii=False)
                }
            })
        return self._normalize_tool_invoke_response(text, tool_calls)

    def set_generation_config(self, temperature=0.7, top_p=1, top_k=40, max_output_tokens=8192):
        self.generation_config = {
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "max_output_tokens": max_output_tokens,
        }
        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-exp",
            generation_config=self.generation_config
        )
        self.chat = self.model.start_chat()

    def audio_chat(self, message: str, audio_path: str) -> str:
        """
        Process a text message and audio file, returning the LLM's text response.
        """
        try:
            audio_file = genai.upload_file(audio_path)
            response = self.model.generate_content([audio_file, message])
            self._add_to_history("user", f"{message} [Audio: {audio_path}]")
            self._add_to_history("assistant", response.text)
            return response.text
        except Exception as e:
            error_msg = f"Error processing audio chat: {str(e)}"
            logging.error(error_msg)
            return error_msg

    def video_chat(self, message: str, video_path: str) -> str:
        """
        Process a text message and video file, returning the LLM's text response.
        """
        try:
            video_file = genai.upload_file(video_path)
            
            # Wait for video processing if needed
            while hasattr(video_file, 'state') and video_file.state.name == "PROCESSING":
                time.sleep(1)
                video_file = genai.get_file(video_file.name)

            if hasattr(video_file, 'state') and video_file.state.name == "FAILED":
                raise ValueError("Video processing failed")

            response = self.model.generate_content(
                [video_file, message],
                request_options={"timeout": 600}
            )
            
            self._add_to_history("user", f"{message} [Video: {video_path}]")
            self._add_to_history("assistant", response.text)
            return response.text
            
        except Exception as e:
            error_msg = f"Error processing video chat: {str(e)}"
            logging.error(error_msg)
            return error_msg

    def clear_chat(self):
        self.chat = self.model.start_chat()
        self.history = []

    def get_stats(self):
        return self.stat

    def get_chat_history(self):
        return self._get_chat_history()

