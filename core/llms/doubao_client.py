import json
from typing import Iterator, List, Dict, Any, Optional, Tuple, Union
from ._llm_api_client import LLMApiClient
from ..utils.config_setting import Config
from volcenginesdkarkruntime import Ark

class DoubaoApiClient(LLMApiClient):
    def __init__(self):
        config = Config()
        self.api_key = config.get("volcengine_api_key")
        self.model = config.get("volcengine_doubao")
        
        # 使用自定义配置初始化 Ark 客户端
        self.client = Ark(api_key=self.api_key)
        
        self.history: List[Dict[str, str]] = []
        self.stats: Dict[str, int] = {
            "call_count": {"text_chat": 0, "image_chat": 0, "tool_chat": 0},
            "total_tokens": 0
        }
        
        # 设置默认参数
        self.max_tokens = 5000
        self.stop = None
        self.temperature = 1
        self.top_p = 1
        self.frequency_penalty = 1

    def text_chat(self, message: str, is_stream: bool = False) -> Union[str, Iterator[str]]:
        self.history.append({"role": "user", "content": message})
        
        if is_stream:
            return self._stream_response(self.history)
        else:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.history,
                max_tokens=self.max_tokens,
                stop=self.stop,
                temperature=self.temperature,
                top_p=self.top_p,
                frequency_penalty=self.frequency_penalty
            )
            assistant_message = response.choices[0].message.content
            self.history.append({"role": "assistant", "content": assistant_message})
            self.stats["call_count"]["text_chat"] += 1
            self.stats["total_tokens"] += response.usage.total_tokens
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
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.history,
            max_tokens=self.max_tokens,
            stop=self.stop,
            temperature=self.temperature,
            top_p=self.top_p,
            frequency_penalty=self.frequency_penalty
        )
        assistant_message = response.choices[0].message.content
        self.history.append({"role": "assistant", "content": assistant_message})
        self.stats["call_count"]["image_chat"] += 1
        self.stats["total_tokens"] += response.usage.total_tokens
        return assistant_message

    def one_chat(self, message: Union[str, List[Union[str, Any]]], is_stream: bool = False) -> Union[str, Iterator[str]]:
        messages = [{"role": "user", "content": message}] if isinstance(message, str) else message
        
        if is_stream:
            return self._stream_response(messages)
        else:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                stop=self.stop,
                temperature=self.temperature,
                top_p=self.top_p,
                frequency_penalty=self.frequency_penalty
            )
            assistant_message = response.choices[0].message.content
            self.stats["call_count"]["text_chat"] += 1
            self.stats["total_tokens"] += response.usage.total_tokens
            return assistant_message

    def _stream_response(self, messages: List[Dict[str, str]]) -> Iterator[str]:
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
            max_tokens=self.max_tokens,
            stop=self.stop,
            temperature=self.temperature,
            top_p=self.top_p,
            frequency_penalty=self.frequency_penalty
        )
        full_response = ""
        for chunk in stream:
            if chunk.choices:
                content = chunk.choices[0].delta.content
                if content:
                    full_response += content
                    yield content
        self.history.append({"role": "assistant", "content": full_response})
        
        self.stats["call_count"]["text_chat"] += 1
        self.stats["total_tokens"] += sum(chunk.usage.total_tokens for chunk in stream)

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
        
        request = {
            "model": self.model,
            "messages": self.history,
            "tools": tools,
            "max_tokens": self.max_tokens,
            "stop": self.stop,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty
        }

        completion = self.client.chat.completions.create(**request)
        
        if completion.choices[0].message.tool_calls:
            tool_call = completion.choices[0].message.tool_calls[0]
            self.history.append(completion.choices[0].message.dict())

            # Execute the function
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
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
                "tool_call_id": tool_call.id,
                "content": str(result),
                "name": function_name,
            })

            # Get the final response from the model
            final_completion = self.client.chat.completions.create(**request)
            final_response = final_completion.choices[0].message.content

            self.history.append({"role": "assistant", "content": final_response})
            self.stats["call_count"]["tool_chat"] += 1
            self.stats["total_tokens"] += completion.usage.total_tokens + final_completion.usage.total_tokens

            return final_response
        else:
            # If no tool was called, return the initial response
            assistant_message = completion.choices[0].message.content
            self.history.append({"role": "assistant", "content": assistant_message})
            self.stats["call_count"]["tool_chat"] += 1
            self.stats["total_tokens"] += completion.usage.total_tokens
            return assistant_message