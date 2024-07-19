import json
import requests
from typing import Generator, Iterator, List, Dict, Any, Union
from ._llm_api_client import LLMApiClient

class BaichuanClient(LLMApiClient):
    def __init__(self, api_key: str, secret_key: str, model: str = "Baichuan2-53B"):
        self.api_key = api_key
        self.secret_key = secret_key
        self.model = model
        self.base_url = "https://api.baichuan-ai.com/v1/chat"
        self.conversation_history: List[Dict[str, str]] = []
        self.parameters: Dict[str, Any] = {
            "temperature": 0.3,
            "top_k": 20,
            "top_p": 0.7,
            "with_search_enhance": False,
            "stream": False,
            "max_new_tokens": 2048,  # 最大输出长度，可选值：[1,2048]，默认值：2048
        }
        self.stats: Dict[str, int] = {
            "api_calls": 0,
            "total_tokens": 0
        }

    def _make_request(self, messages: List[Dict[str, str]], stream: bool = False) -> Union[Dict, requests.Response]:
        url = f"{self.base_url}/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}:{self.secret_key}"
        }
        payload = {
            "model": self.model,
            "messages": messages,
            **self.parameters,
            "stream": stream
        }

        self.stats["api_calls"] += 1
        response = requests.post(url, headers=headers, json=payload, stream=stream)
        response.raise_for_status()

        return response if stream else response.json()

    def text_chat(self, message: str, is_stream: bool = False) -> Union[str, Iterator[str]]:
        self.conversation_history.append({"role": "user", "content": message})
        response = self._make_request(self.conversation_history, is_stream)

        if is_stream:
            return self._process_stream_response(response)
        else:
            assistant_message = response['choices'][0]['message']['content']
            self.conversation_history.append({"role": "assistant", "content": assistant_message})
            self.stats["total_tokens"] += response['usage']['total_tokens']
            return assistant_message

    def _process_stream_response(self, response: requests.Response) -> Iterator[str]:
        full_response = ""
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    if 'choices' in data and len(data['choices']) > 0:
                        delta = data['choices'][0].get('delta', {})
                        content = delta.get('content', '')
                        if content:
                            full_response += content
                            yield content
                        if 'usage' in data:
                            self.stats["total_tokens"] += data['usage']['total_tokens']
        self.conversation_history.append({"role": "assistant", "content": full_response})

    def one_chat(self, message: Union[str, List[Union[str, Any]]], is_stream: bool = False) -> Union[str, Iterator[str]]:
        if isinstance(message, str):
            messages = [{"role": "user", "content": message}]
        else:
            messages = message
        response = self._make_request(messages, is_stream)

        if is_stream:
            return self._process_stream_response(response)
        else:
            self.stats["total_tokens"] += response['usage']['total_tokens']
            return response['choices'][0]['message']['content']

    def tool_chat(self, user_message: str, tools: List[Dict[str, Any]], function_module: Any, is_stream: bool = False) -> Union[str, Iterator[str]]:
        # Baichuan API currently doesn't support function calling
        raise NotImplementedError("Baichuan API does not support function calling.")

    def audio_chat(self, message: str, audio_path: str) -> str:
        raise NotImplementedError("Baichuan API does not support audio chat.")

    def video_chat(self, message: str, video_path: str) -> str:
        raise NotImplementedError("Baichuan API does not support video chat.")

    def clear_chat(self):
        self.conversation_history.clear()

    def get_stats(self) -> Dict[str, Any]:
        return self.stats

    def set_parameters(self, **kwargs):
        valid_params = ["temperature", "top_k", "top_p", "with_search_enhance", "max_new_tokens"]
        for key, value in kwargs.items():
            if key in valid_params:
                self.parameters[key] = value
            else:
                print(f"Warning: {key} is not a valid parameter for Baichuan API and will be ignored.")