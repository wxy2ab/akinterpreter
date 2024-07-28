import json
import requests
from typing import Iterator, List, Dict, Any, Union
from ..utils.config_setting import Config
from ..utils.handle_max_tokens import handle_max_tokens
from ._llm_api_client import LLMApiClient

class SimpleDoubaoClient(LLMApiClient):
    def __init__(self):
        config = Config()
        self.api_key = config.get("volcengine_api_key")
        self.model = config.get("volcengine_doubao")
        self.base_url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
        
        self.history: List[Dict[str, str]] = []
        self.stats: Dict[str, int] = {
            "call_count": {"text_chat": 0, "image_chat": 0, "tool_chat": 0},
            "total_tokens": 0
        }
        
        # Set default parameters
        self.max_tokens = 4096
        self.stop = None
        self.temperature = 1
        self.top_p = 1
        self.frequency_penalty = 1

    def _make_request(self, payload: Dict[str, Any], stream: bool = False) -> Union[Dict[str, Any], Iterator[Dict[str, Any]]]:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        response = requests.post(self.base_url, json=payload, headers=headers, stream=stream)
        response.raise_for_status()
        
        if stream:
            return self._parse_stream_response(response)
        else:
            return response.json()

    def _parse_stream_response(self, response: requests.Response) -> Iterator[Dict[str, Any]]:
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    line = line[6:]  # Remove 'data: ' prefix
                    if line == '[DONE]':
                        break  # End of stream
                    else:
                        try:
                            yield json.loads(line)
                        except json.JSONDecodeError:
                            print(f"Failed to parse JSON: {line}")

    @handle_max_tokens
    def text_chat(self, message: str, is_stream: bool = False) -> Union[str, Iterator[str]]:
        self.history.append({"role": "user", "content": message})
        
        payload = {
            "model": self.model,
            "messages": self.history,
            "max_tokens": self.max_tokens,
            "stop": self.stop,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "stream": is_stream
        }
        
        if is_stream:
            return self._stream_response(payload)
        else:
            response = self._make_request(payload)
            assistant_message = response['choices'][0]['message']['content']
            self.history.append({"role": "assistant", "content": assistant_message})
            self.stats["call_count"]["text_chat"] += 1
            self.stats["total_tokens"] += response['usage']['total_tokens']
            return assistant_message

    def image_chat(self, message: str, image_path: str) -> str:
        import base64
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')

        content = [
            {"type": "text", "text": message},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
        ]
        self.history.append({"role": "user", "content": content})
        
        payload = {
            "model": self.model,
            "messages": self.history,
            "max_tokens": self.max_tokens,
            "stop": self.stop,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty
        }
        
        response = self._make_request(payload)
        assistant_message = response['choices'][0]['message']['content']
        self.history.append({"role": "assistant", "content": assistant_message})
        self.stats["call_count"]["image_chat"] += 1
        self.stats["total_tokens"] += response['usage']['total_tokens']
        return assistant_message

    def one_chat(self, message: Union[str, List[Union[str, Any]]], is_stream: bool = False) -> Union[str, Iterator[str]]:
        messages = [{"role": "user", "content": message}] if isinstance(message, str) else message
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "stop": self.stop,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "stream": is_stream
        }
        
        if is_stream:
            return self._stream_response(payload)
        else:
            response = self._make_request(payload)
            assistant_message = response['choices'][0]['message']['content']
            self.stats["call_count"]["text_chat"] += 1
            self.stats["total_tokens"] += response['usage']['total_tokens']
            return assistant_message

    def _stream_response(self, payload: Dict[str, Any]) -> Iterator[str]:
        stream = self._make_request(payload, stream=True)
        full_response = ""
        for chunk in stream:
            if 'choices' in chunk and chunk['choices']:
                content = chunk['choices'][0].get('delta', {}).get('content')
                if content:
                    full_response += content
                    yield content
        self.history.append({"role": "assistant", "content": full_response})
        
        self.stats["call_count"]["text_chat"] += 1
        # Note: We can't accurately count tokens for streaming responses without additional API calls

    def clear_chat(self):
        self.history.clear()

    def get_stats(self) -> Dict[str, Any]:
        return self.stats

    def audio_chat(self, message: str, audio_path: str) -> str:
        raise NotImplementedError("Audio chat is not supported by DoubaoApiClient")

    def video_chat(self, message: str, video_path: str) -> str:
        raise NotImplementedError("Video chat is not supported by DoubaoApiClient")
    
    def tool_chat(self, user_message: str, tools: List[Dict[str, Any]], function_module: Any, is_stream: bool = False) -> Union[str, Iterator[str]]:
        if is_stream:
            raise NotImplementedError("Streaming is not supported for tool_chat in DoubaoApiClient")

        self.history.append({"role": "user", "content": user_message})
        
        payload = {
            "model": self.model,
            "messages": self.history,
            "tools": tools,
            "max_tokens": self.max_tokens,
            "stop": self.stop,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty
        }

        response = self._make_request(payload)
        
        if 'tool_calls' in response['choices'][0]['message']:
            tool_call = response['choices'][0]['message']['tool_calls'][0]
            self.history.append(response['choices'][0]['message'])

            # Execute the function
            function_name = tool_call['function']['name']
            function_args = json.loads(tool_call['function']['arguments'])
            if hasattr(function_module, function_name):
                function = getattr(function_module, function_name)
                try:
                    result = function(**function_args)
                except Exception as e:
                    result = f"Error executing {function_name}: {str(e)}"
            else:
                result = f"Function {function_name} not found in the provided module."

            # Add the function result to the conversation
            self.history.append({
                "role": "tool",
                "tool_call_id": tool_call['id'],
                "content": str(result),
                "name": function_name,
            })

            # Get the final response from the model
            final_response = self._make_request(payload)
            final_message = final_response['choices'][0]['message']['content']

            self.history.append({"role": "assistant", "content": final_message})
            self.stats["call_count"]["tool_chat"] += 1
            self.stats["total_tokens"] += response['usage']['total_tokens'] + final_response['usage']['total_tokens']

            return final_message
        else:
            # If no tool was called, return the initial response
            assistant_message = response['choices'][0]['message']['content']
            self.history.append({"role": "assistant", "content": assistant_message})
            self.stats["call_count"]["tool_chat"] += 1
            self.stats["total_tokens"] += response['usage']['total_tokens']
            return assistant_message