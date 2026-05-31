



import json
import time
from typing import Any, Dict, Generator, Iterator, List, Union

from ratelimit import limits, sleep_and_retry
import requests
from requests.exceptions import ChunkedEncodingError, ConnectionError as RequestsConnectionError, HTTPError, ProxyError, Timeout
from core.llms._llm_api_client import LLMApiClient
from  ..utils.config_setting import Config
from ..utils.handle_max_tokens import handle_max_tokens
from ..utils.log import logger


class MiniMaxClient(LLMApiClient):
    def __init__(self, api_key: str = "", model: str = "MiniMax-M2.7-highspeed"):
        config = Config()
        if api_key == "" and config.has_key("minimax_api_key"):
            api_key = config.get("minimax_api_key")
        self.api_key = api_key
        if model is None or model == "":
            model = "MiniMax-M2.7-highspeed"
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
            "mask_sensitive_info":False
        }
        self.stats: Dict[str, int] = {
            "api_calls": 0,
            "total_tokens": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
        }
        self.debug = False
        self._last_id = ""
        self.request_timeout = (30, 600)
        self.max_retries = 4
        self.retry_backoff_base_seconds = 2
        self.session = requests.Session()

    def _is_retryable_exception(self, exc: Exception) -> bool:
        if isinstance(exc, (RequestsConnectionError, ProxyError, Timeout, ChunkedEncodingError)):
            return True
        if isinstance(exc, HTTPError) and exc.response is not None:
            return exc.response.status_code in {408, 409, 425, 429, 500, 502, 503, 504, 520, 521, 522, 524}
        return False

    def _request_with_retry(self, payload: Dict[str, Any], stream: bool) -> requests.Response:
        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            self.stats["api_calls"] += 1
            try:
                response = self.session.post(
                    self.base_url,
                    headers=self.headers,
                    json=payload,
                    stream=stream,
                    timeout=self.request_timeout,
                )
                response.raise_for_status()
                return response
            except Exception as exc:
                last_error = exc
                if not self._is_retryable_exception(exc) or attempt >= self.max_retries:
                    raise
                delay_seconds = min(20, self.retry_backoff_base_seconds * (2 ** (attempt - 1)))
                logger.warning(
                    f"MiniMax request failed (attempt={attempt}/{self.max_retries}, error_type={type(exc).__name__}), retrying in {delay_seconds}s: {exc}"
                )
                time.sleep(delay_seconds)
        if last_error is not None:
            raise last_error
        raise RuntimeError("MiniMax request failed without an exception")

    _RETRYABLE_API_STATUS_KEYWORDS = {"unknown error", "rate limit", "server busy", "internal error", "service unavailable"}

    def _is_retryable_api_error(self, result: Dict) -> bool:
        base_resp = result.get("base_resp")
        if not base_resp or base_resp.get("status_code", 0) == 0:
            return False
        msg = str(base_resp.get("status_msg", "")).lower()
        if any(kw in msg for kw in self._RETRYABLE_API_STATUS_KEYWORDS):
            return True
        return False

    def _make_request(self, messages: List[Dict[str, str]], stream: bool = False, **kwargs) -> Union[Dict, Generator]:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            **self.parameters,
            **kwargs
        }

        if stream:
            response = self._request_with_retry(payload, stream=True)
            return self._handle_stream_response(response)

        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self._request_with_retry(payload, stream=False)
                result = response.json()

                if self.debug and "id" in result:
                    logger.info(f"response ID: {result['id']}")

                if self._is_retryable_api_error(result) and attempt < self.max_retries:
                    msg = result.get("base_resp", {}).get("status_msg", "unknown")
                    delay = min(20, self.retry_backoff_base_seconds * (2 ** (attempt - 1)))
                    logger.warning(
                        "MiniMax API error (attempt=%d/%d): %s, retrying in %ds",
                        attempt, self.max_retries, msg, delay,
                    )
                    time.sleep(delay)
                    continue

                return result
            except Exception as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    raise
                delay = min(20, self.retry_backoff_base_seconds * (2 ** (attempt - 1)))
                logger.warning(
                    "MiniMax request failed (attempt=%d/%d): %s, retrying in %ds",
                    attempt, self.max_retries, exc, delay,
                )
                time.sleep(delay)

        if last_error is not None:
            raise last_error
        raise RuntimeError("MiniMax request failed without an exception")

    def _handle_stream_response(self, response: requests.Response) -> Generator:
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                try:
                    if line.startswith("data: "):
                        json_line = line[6:]
                        chunk_data = json.loads(json_line)
                    else:
                        chunk_data = json.loads(line.decode('utf-8'))
                    if self.debug and "id" in chunk_data and self._last_id!=chunk_data['id']:
                        logger.info(f"response ID: {chunk_data['id']}")
                        self._last_id=chunk_data['id']
                except:
                    pass
                if line.startswith("data: "):
                    yield json.loads(line[6:])

    def _update_usage_stats(self, usage: Dict[str, Any] | None) -> None:
        if not usage:
            return

        def _to_int(value: Any) -> int:
            try:
                return int(value or 0)
            except (TypeError, ValueError):
                return 0

        prompt_tokens = _to_int(usage.get("prompt_tokens"))
        completion_tokens = _to_int(usage.get("completion_tokens"))
        total_tokens = _to_int(usage.get("total_tokens"))
        if total_tokens == 0:
            total_tokens = prompt_tokens + completion_tokens

        self.stats["prompt_tokens"] += prompt_tokens
        self.stats["completion_tokens"] += completion_tokens
        self.stats["total_tokens"] += total_tokens

    @handle_max_tokens
    def text_chat(self, message: str, is_stream: bool = False) -> Union[str, Iterator[str]]:
        self.history.append({"role": "user", "content": message})
        response = self._make_request(self.history, is_stream)

        if is_stream:
            return self._process_stream_response(response)
        else:
            choices = response.get('choices')
            if not choices or not choices[0].get('message'):
                raise Exception(f"MiniMax API returned invalid response: {str(response)[:200]}")
            assistant_message = choices[0]['message'].get('content', '')
            self.history.append({"role": "assistant", "content": assistant_message})
            self._update_usage_stats(response.get('usage'))
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
                self._update_usage_stats(chunk['usage'])
        self.history.append({"role": "assistant", "content": full_response})

    @sleep_and_retry
    @limits(calls=20, period=1)
    def one_chat(self, message: Union[str, List[Union[str, Any]]], is_stream: bool = False) -> Union[str, Iterator[str]]:
        if isinstance(message, str):
            messages = [{"role": "user", "content": message}]
        else:
            messages = message
        response = self._make_request(messages, is_stream)

        if is_stream:
            return self._process_stream_response(response)
        else:
            if 'base_resp' in response and response['base_resp']['status_code']!=0:
                raise Exception(response['base_resp']['status_msg'])
            self._update_usage_stats(response.get('usage'))
            choices = response.get('choices')
            if not choices:
                raise Exception(f"MiniMax API returned empty choices: {str(response)[:200]}")
            message_obj = choices[0].get('message')
            if not message_obj:
                raise Exception(f"MiniMax API returned empty message in choices[0]: {str(choices[0])[:200]}")
            return message_obj.get('content', '')

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
            choices = response.get('choices')
            if not choices or not choices[0].get('message'):
                raise Exception(f"MiniMax API returned invalid response: {str(response)[:200]}")
            assistant_message = choices[0]['message'].get('content', '')
            self.history.append({"role": "assistant", "content": assistant_message})
            self._update_usage_stats(response.get('usage'))
            return assistant_message

    def tool_invoke(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        payload = {"tools": tools, "tool_choice": "auto"}
        response: Dict[str, Any] = {}
        for attempt in range(1, self.max_retries + 1):
            response = self._make_request(messages, False, **payload)
            choices = response.get('choices')
            if choices and choices[0].get('message'):
                break
            if attempt >= self.max_retries:
                raise Exception(f"MiniMax API returned invalid response after {self.max_retries} attempts: {str(response)[:200]}")
            delay = min(20, self.retry_backoff_base_seconds * (2 ** (attempt - 1)))
            logger.warning("MiniMax tool_invoke got empty choices (attempt=%d/%d), retrying in %ds", attempt, self.max_retries, delay)
            time.sleep(delay)

        message = choices[0]['message']
        content = message.get('content', '') or ''
        tool_calls_raw = message.get('tool_calls') or []

        self._update_usage_stats(response.get('usage'))

        normalized_calls = []
        for tc in tool_calls_raw:
            func = tc.get('function', {})
            args = func.get('arguments', '{}')
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}
            normalized_calls.append({
                "tool_name": func.get('name', ''),
                "arguments": args,
                "tool_use_id": tc.get('id', ''),
            })
        return {"content": content, "tool_calls": normalized_calls}

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
