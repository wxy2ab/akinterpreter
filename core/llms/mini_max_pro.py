import json
from typing import Any, Dict, Generator, Iterator, List, Union

import requests
from core.llms._llm_api_client import LLMApiClient
from ..utils.config_setting import Config
from ..utils.handle_max_tokens import handle_max_tokens
from ..utils.log import logger

class MiniMaxProClient(LLMApiClient):
    def __init__(self, model: str = "abab6.5s-chat"):
        config = Config()
        self.api_key = config.get("minimax_api_key")
        self.model = model
        self.base_url = f"https://api.minimax.chat/v1/text/chatcompletion_pro"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        self.history: List[Dict[str, str]] = []
        self.parameters: Dict[str, Any] = {
            "temperature": 0.1,
            "top_p": 0.95,
            "tokens_to_generate": 8000,
            "mask_sensitive_info": False,
            "bot_setting": [
                {
                    "bot_name": "信息处理专家",
                    "content": "你擅长信息处理，严格遵循指令，输出结构完整的JSON"
                }
            ],
            "reply_constraints": {"sender_type": "BOT", "sender_name": "信息处理专家"},
        }
        self.stats: Dict[str, int] = {
            "api_calls": 0,
            "total_tokens": 0
        }
        self.debug = False
        self._last_id = ""

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
        if self.debug and not stream:
            content = response.json()
            if "id" in content:
                logger.info(f"response ID: {content['id']}")
        response.raise_for_status()

        if stream:
            return self._handle_stream_response(response)
        else:
            return response.json()

    def _handle_stream_response(self, response: requests.Response) -> Generator:
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                try:
                    if line.startswith("data: "):
                        json_line = line[6:]
                        chunk_data = json.loads(json_line)
                    else:
                        chunk_data = json.loads(line)
                    if self.debug and "id" in chunk_data and self._last_id != chunk_data['id']:
                        logger.info(f"response ID: {chunk_data['id']}")
                        self._last_id = chunk_data['id']
                except json.JSONDecodeError:
                    pass
                if line.startswith("data: "):
                    yield json.loads(line[6:])

    @handle_max_tokens
    def text_chat(self, message: str, is_stream: bool = False) -> Union[str, Iterator[str]]:
        self.history.append({"sender_type": "USER", "sender_name": "USER", "text": message})
        response = self._make_request(self.history, is_stream)

        if is_stream:
            return self._process_stream_response(response)
        else:
            assistant_message = response['reply']
            self.history.append({"sender_type": "BOT", "sender_name": "MM智能助理", "text": assistant_message})
            self.stats["total_tokens"] += response['usage']['total_tokens']
            return assistant_message

    def _process_stream_response(self, response: Generator) -> Iterator[str]:
        full_response = ""
        for chunk in response:
            if 'choices' in chunk and len(chunk['choices']) > 0:
                if 'delta' in chunk['choices'][0]:
                    content = chunk['choices'][0]['delta'].get('text', '')
                    full_response += content
                    yield content
                elif 'messages' in chunk['choices'][0]:
                    content = chunk['choices'][0]['messages'][0].get('text', '')
                    if content != full_response:
                        yield content[len(full_response):]
                        full_response = content
            if 'usage' in chunk:
                self.stats["total_tokens"] += chunk['usage']['total_tokens']
        self.history.append({"sender_type": "BOT", "sender_name": "MM智能助理", "text": full_response})

    def one_chat(self, message: Union[str, List[Union[str, Any]]], is_stream: bool = False) -> Union[str, Iterator[str]]:
        if isinstance(message, str):
            messages = [{"sender_type": "USER", "sender_name": "USER", "text": message}]
        else:
            messages = message
        response = self._make_request(messages, is_stream)

        if is_stream:
            return self._process_stream_response(response)
        else:
            if 'base_resp' in response and response['base_resp']['status_code'] != 0:
                raise Exception(response['base_resp']['status_msg'])
            self.stats["total_tokens"] += response['usage']['total_tokens']
            return response['reply']

    def tool_chat(self, user_message: str, tools: List[Dict[str, Any]], function_module: Any, is_stream: bool = False) -> Union[str, Iterator[str]]:
        self.history.append({"sender_type": "USER", "sender_name": "USER", "text": user_message})
        payload = {
            "functions": tools,
            "function_call": "auto"
        }
        response = self._make_request(self.history, is_stream, **payload)

        if is_stream:
            return self._process_stream_response(response)
        else:
            assistant_message = response['reply']
            self.history.append({"sender_type": "BOT", "sender_name": "MM智能助理", "text": assistant_message})
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