



import json
from typing import Any, Dict, Generator, Iterator, List, Union

import requests
from core.llms._llm_api_client import LLMApiClient
from  ..utils.config_setting import Config
from ..utils.handle_max_tokens import handle_max_tokens

class MiniMaxClient(LLMApiClient):
    def __init__(self,  model: str = "abab6.5s-chat"):
        config = Config()
        api_key = config.get("minimax_api_key")
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.minimax.chat/v1/text/chatcompletion_v2"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        self.history: List[Dict[str, str]] = []
        self.parameters: Dict[str, Any] = {
            "temperature": 0.9,
            "top_p": 1,
            "max_tokens": 2048
        }
        self.stats: Dict[str, int] = {
            "api_calls": 0,
            "total_tokens": 0
        }

    def _make_request(self, messages: List[Dict[str, str]], stream: bool = False, **kwargs) -> Union[Dict, Generator]:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            **self.parameters,
            **kwargs
        }
        
        self.stats["api_calls"] += 1
        response = requests.post(self.base_url, headers=self.headers, json=payload, stream=stream)
        response.raise_for_status()

        if stream:
            return self._handle_stream_response(response)
        else:
            return response.json()

    def _handle_stream_response(self, response: requests.Response) -> Generator:
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith("data: "):
                    yield json.loads(line[6:])

    @handle_max_tokens
    def text_chat(self, message: str, is_stream: bool = False) -> Union[str, Iterator[str]]:
        self.history.append({"role": "user", "content": message})
        response = self._make_request(self.history, is_stream)

        if is_stream:
            return self._process_stream_response(response)
        else:
            assistant_message = response['choices'][0]['message']['content']
            self.history.append({"role": "assistant", "content": assistant_message})
            self.stats["total_tokens"] += response['usage']['total_tokens']
            return assistant_message

    def _process_stream_response(self, response: Generator) -> Iterator[str]:
        full_response = ""
        for chunk in response:
            if 'choices' in chunk and len(chunk['choices']) > 0:
                if 'delta' in chunk['choices'][0]:
                    content = chunk['choices'][0]['delta'].get('content', '')
                    full_response += content
                    yield content
                elif 'message' in chunk['choices'][0]:
                    content = chunk['choices'][0]['message'].get('content', '')
                    if content != full_response:
                        yield content[len(full_response):]
                        full_response = content
            if 'usage' in chunk:
                self.stats["total_tokens"] += chunk['usage']['total_tokens']
        self.history.append({"role": "assistant", "content": full_response})

    def one_chat(self, message: Union[str, List[Union[str, Any]]], is_stream: bool = False) -> Union[str, Iterator[str]]:
        if isinstance(message, str):
            messages = [{"role": "user", "content": message}]
        else:
            messages = message
        response = self._make_request(messages, is_stream)

        if is_stream:
            return self._process_stream_response(response)
        else:
            #self.stats["total_tokens"] += response['usage']['total_tokens']
            return response['choices'][0]['message']['content']

    def tool_chat(self, user_message: str, tools: List[Dict[str, Any]], function_module: Any, is_stream: bool = False) -> Union[str, Iterator[str]]:
        self.history.append({"role": "user", "content": user_message})
        payload = {
            "tools": tools,
            "tool_choice": "auto"
        }
        response = self._make_request(self.history, is_stream, **payload)

        if is_stream:
            return self._process_stream_response(response)
        else:
            assistant_message = response['choices'][0]['message']['content']
            self.history.append({"role": "assistant", "content": assistant_message})
            self.stats["total_tokens"] += response['usage']['total_tokens']
            return assistant_message

    def audio_chat(self, message: str, audio_path: str) -> str:
        raise NotImplementedError("MiniMax API does not support audio chat.")

    def video_chat(self, message: str, video_path: str) -> str:
        raise NotImplementedError("MiniMax API does not support video chat.")

    def clear_chat(self):
        self.history.clear()

    def get_stats(self) -> Dict[str, Any]:
        return self.stats

    def set_parameters(self, **kwargs):
        super().set_parameters(**kwargs)