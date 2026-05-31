import os
import base64
import json
import time
import uuid
from typing import Any, Dict, Iterator, List, Optional, Union

import httpx

from ._llm_api_client import LLMApiClient
from ..utils.config_setting import Config
from ..utils.handle_max_tokens import handle_max_tokens
from ..utils.log import logger


# HTTP status codes that indicate transient server-side issues. Retrying these
# with exponential backoff is safe for idempotent JSON requests.
_RETRYABLE_STATUS_CODES = frozenset({408, 409, 425, 429, 500, 502, 503, 504, 520, 521, 522, 524})


class OpenAIHttpClient(LLMApiClient):

    def __init__(self,
                 api_key: str = "",
                 model: str = "gpt-5.4-mini",
                 base_url: str = "https://api.openai.com/v1",
                 max_tokens: Optional[int] = None,
                 temperature: Optional[float] = 0.7,
                 top_p: Optional[float] = 1,
                 presence_penalty: Optional[float] = 0,
                 frequency_penalty: Optional[float] = 0,
                 stop: Union[str, List[str], None] = None,
                 client_request_id: Optional[str] = None,
                 max_retries: int = 4,
                 retry_backoff_base_seconds: float = 2.0,
                 retry_backoff_cap_seconds: float = 20.0):
        config = Config()
        if api_key == "" and config.has_key("openai_api_key"):
            api_key = config.get("openai_api_key")
        if api_key == "":
            api_key = os.getenv("OPENAI_API_KEY", "") or ""

        self.api_key = self._sanitize_api_key(api_key)
        # Defensive: callers sometimes include backticks/whitespace.
        self.base_url = base_url.strip().strip("`").strip().rstrip("/")
        self.client_request_id = client_request_id.strip() if isinstance(client_request_id, str) and client_request_id.strip() else None
        self.http_client = httpx.Client(
            limits=httpx.Limits(max_keepalive_connections=100, max_connections=200),
            timeout=httpx.Timeout(timeout=600.0, connect=60.0, read=600.0, write=120.0)
        )
        self.chat_count = 0
        self.token_count = 0
        self.prompt_token_count = 0
        self.completion_token_count = 0
        self.history: List[Dict[str, Any]] = []
        self.model = model
        self.max_output_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.presence_penalty = presence_penalty
        self.frequency_penalty = frequency_penalty
        self.stop = stop
        self.wire_api = "httpx"
        # Retry configuration. Without this, transient 429/5xx/network errors
        # under concurrent load (e.g. story_eval running 10 dimensions in
        # parallel across many stories) propagate immediately to the caller
        # and cause later evaluations to silently score 0.0 — producing a
        # "early-high, later-extremely-low" pattern. Every other client in
        # this repo (OpenAIClient via SDK, MoonShotClient, MiniMaxClient, ...)
        # already has retries, so this client must too.
        self.max_retries = max(1, int(max_retries))
        self.retry_backoff_base_seconds = float(retry_backoff_base_seconds)
        self.retry_backoff_cap_seconds = float(retry_backoff_cap_seconds)

    @staticmethod
    def _sanitize_api_key(api_key: Optional[str]) -> str:
        if not isinstance(api_key, str):
            return ""
        sanitized = api_key.strip().strip("`").strip().strip("\"'")
        if sanitized.lower().startswith("bearer "):
            sanitized = sanitized[7:].strip()
        return sanitized

    def _ensure_api_key_configured(self) -> None:
        if self.api_key:
            return
        raise ValueError(
            "OpenAI API key is missing. Please set `openai_api_key` in `setting.ini` "
            "or the `OPENAI_API_KEY` environment variable."
        )

    def _raise_http_error(self, exc: httpx.HTTPStatusError) -> None:
        status_code = exc.response.status_code
        if status_code == 401:
            raise PermissionError(
                "OpenAI authentication failed with 401 Unauthorized. "
                "Check that `openai_api_key` in `setting.ini` or `OPENAI_API_KEY` "
                "contains a valid active API key for the target endpoint."
            ) from exc
        raise exc

    @staticmethod
    def _is_retryable_exception(exc: Exception) -> bool:
        if isinstance(exc, httpx.HTTPStatusError):
            return exc.response.status_code in _RETRYABLE_STATUS_CODES
        if isinstance(exc, (
            httpx.TimeoutException,
            httpx.ConnectError,
            httpx.ReadError,
            httpx.WriteError,
            httpx.RemoteProtocolError,
            httpx.PoolTimeout,
        )):
            return True
        # NetworkError is a base class catching the rest of the transport-level
        # failures we want to retry (e.g. NetworkError thrown by proxies).
        if isinstance(exc, httpx.NetworkError):
            return True
        return False

    def _retry_delay_seconds(self, attempt: int, response: Optional[httpx.Response] = None) -> float:
        # Honour Retry-After when the server provides one. OpenAI sets it on 429
        # and sometimes on 503; respecting it avoids hammering the endpoint.
        if response is not None:
            retry_after = response.headers.get("retry-after")
            if retry_after:
                try:
                    return min(self.retry_backoff_cap_seconds, float(retry_after))
                except ValueError:
                    pass
        return min(
            self.retry_backoff_cap_seconds,
            self.retry_backoff_base_seconds * (2 ** max(0, attempt - 1)),
        )

    @property
    def max_tokens(self) -> Optional[int]:
        return self.max_output_tokens

    @max_tokens.setter
    def max_tokens(self, value: Optional[int]) -> None:
        self.max_output_tokens = value

    def set_system_message(self,
                           system_message: str = "你是个智能助手，你遵循指令和写代码的能力超级棒."):
        self.history = [{"role": "system", "content": system_message}]

    @handle_max_tokens
    def text_chat(self,
                  message: str,
                  is_stream: bool = False) -> Union[str, Iterator[str]]:
        if not self.history:
            self.set_system_message()
        self.history.append({"role": "user", "content": message})
        return self._create_response(self.history, is_stream, track_history=True)

    def one_chat(self,
                 message: Union[str, List[Dict[str, Any]]],
                 is_stream: bool = False) -> Union[str, Iterator[str]]:
        if not self.history:
            self.set_system_message()
        messages = [{
            "role": "user",
            "content": message
        }] if isinstance(message, str) else message
        return self._create_response(messages, is_stream, track_history=False)

    def tool_chat(self,
                  user_message: str,
                  tools: List[Dict[str, Any]],
                  function_module: Any,
                  is_stream: bool = False) -> Union[str, Iterator[str]]:
        if not self.history:
            self.set_system_message()
        self.history.append({"role": "user", "content": user_message})
        if is_stream:
            return self._unified_tool_stream(self.history, tools, function_module)
        response = self._create_chat_completion(
            self.history,
            is_stream=False,
            tools=tools,
            raw_response=True
        )
        return self._process_tool_response(response, tools, function_module)

    def image_chat(self,
                   message: str,
                   image_path_or_url: str,
                   is_stream: bool = False) -> Union[str, Iterator[str]]:
        if not self.history:
            self.set_system_message()

        if image_path_or_url.startswith(("http://", "https://")):
            image_url = image_path_or_url
        else:
            image_url = self._encode_image_to_base64(image_path_or_url)

        self.history.append({
            "role": "user",
            "content": [
                {"type": "text", "text": message},
                {"type": "image_url", "image_url": {"url": image_url}},
            ]
        })
        return self._create_response(self.history, is_stream, track_history=True)

    def audio_chat(self, message: str, audio_path: str) -> str:
        raise NotImplementedError("OpenAI HTTP client does not support audio chat.")

    def video_chat(self, message: str, video_path: str) -> str:
        raise NotImplementedError("OpenAI HTTP client does not support video chat.")

    def clear_chat(self) -> None:
        self.history = []

    def close(self) -> None:
        """Release the underlying httpx connection pool.

        Story-eval style workloads create a fresh client per dimension
        (10 dimensions x N stories x up to 2 attempts), so failing to
        close the pool can leak sockets and file descriptors over a long
        run. Safe to call multiple times.
        """
        client = getattr(self, "http_client", None)
        if client is None:
            return
        try:
            client.close()
        except Exception:
            pass
        self.http_client = None  # type: ignore[assignment]

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_chats": self.chat_count,
            "total_tokens": self.token_count,
            "prompt_tokens": self.prompt_token_count,
            "completion_tokens": self.completion_token_count,
        }

    def tool_invoke(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        response = self._create_chat_completion(
            messages,
            is_stream=False,
            tools=tools,
            raw_response=True
        )
        choices = response.get("choices") or []
        if not choices:
            self._update_stats(response.get("usage"))
            return self._normalize_tool_invoke_response("", None)
        self._update_stats(response.get("usage"))
        message = choices[0].get("message", {})
        return self._normalize_tool_invoke_response(
            message.get("content", "") or "",
            message.get("tool_calls", None)
        )

    def _build_headers(self, request_id: Optional[str] = None) -> Dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        rid = request_id or self.client_request_id
        if rid:
            headers["X-Client-Request-Id"] = rid
        return headers

    def _build_url(self, endpoint: str) -> str:
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    def _request_json(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        self._ensure_api_key_configured()
        url = self._build_url(endpoint)
        last_error: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            # Generate a fresh request id per attempt so upstream proxies that
            # treat X-Client-Request-Id as an idempotency key don't return a
            # cached failure on retry.
            request_id = self.client_request_id or str(uuid.uuid4())
            try:
                response = self.http_client.post(
                    url,
                    headers=self._build_headers(request_id),
                    json=payload,
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                last_error = exc
                if attempt < self.max_retries and self._is_retryable_exception(exc):
                    delay = self._retry_delay_seconds(attempt, exc.response)
                    logger.warning(
                        "OpenAI HTTP request failed (attempt=%d/%d, status=%d), retrying in %.1fs",
                        attempt, self.max_retries, exc.response.status_code, delay,
                    )
                    time.sleep(delay)
                    continue
                # Non-retryable (e.g. 401) or out of retries — surface a
                # clean error.
                self._raise_http_error(exc)
                raise
            except Exception as exc:
                last_error = exc
                if attempt < self.max_retries and self._is_retryable_exception(exc):
                    delay = self._retry_delay_seconds(attempt)
                    logger.warning(
                        "OpenAI HTTP request failed (attempt=%d/%d, error=%s: %s), retrying in %.1fs",
                        attempt, self.max_retries, type(exc).__name__, exc, delay,
                    )
                    time.sleep(delay)
                    continue
                raise

        if last_error is not None:
            raise last_error
        raise RuntimeError("OpenAI HTTP request failed without an exception")

    def _stream_json_lines(self, endpoint: str, payload: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        self._ensure_api_key_configured()
        url = self._build_url(endpoint)
        last_error: Optional[Exception] = None

        # We retry only the connection / opening of the stream. Once we begin
        # yielding parsed events to the caller it's no longer safe to silently
        # retry, because the caller has already observed partial output.
        for attempt in range(1, self.max_retries + 1):
            request_id = self.client_request_id or str(uuid.uuid4())
            try:
                stream_cm = self.http_client.stream(
                    "POST",
                    url,
                    headers=self._build_headers(request_id),
                    json=payload,
                )
                response = stream_cm.__enter__()
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as exc:
                    stream_cm.__exit__(type(exc), exc, exc.__traceback__)
                    last_error = exc
                    if attempt < self.max_retries and self._is_retryable_exception(exc):
                        delay = self._retry_delay_seconds(attempt, exc.response)
                        logger.warning(
                            "OpenAI HTTP stream failed (attempt=%d/%d, status=%d), retrying in %.1fs",
                            attempt, self.max_retries, exc.response.status_code, delay,
                        )
                        time.sleep(delay)
                        continue
                    self._raise_http_error(exc)
                    raise

                try:
                    for line in response.iter_lines():
                        if not line:
                            continue
                        if isinstance(line, bytes):
                            line = line.decode("utf-8")
                        if not line.startswith("data:"):
                            continue
                        data = line[5:].strip()
                        if data == "[DONE]":
                            break
                        try:
                            yield json.loads(data)
                        except json.JSONDecodeError:
                            continue
                    return
                finally:
                    stream_cm.__exit__(None, None, None)
            except Exception as exc:
                last_error = exc
                if attempt < self.max_retries and self._is_retryable_exception(exc):
                    delay = self._retry_delay_seconds(attempt)
                    logger.warning(
                        "OpenAI HTTP stream failed (attempt=%d/%d, error=%s: %s), retrying in %.1fs",
                        attempt, self.max_retries, type(exc).__name__, exc, delay,
                    )
                    time.sleep(delay)
                    continue
                raise

        if last_error is not None:
            raise last_error
        raise RuntimeError("OpenAI HTTP stream failed without an exception")

    def _flatten_message_content(self, content: Any) -> str:
        if content is None:
            return ""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict):
                    if item.get("type") == "text" and item.get("text") is not None:
                        parts.append(str(item.get("text")))
                    elif item.get("text") is not None:
                        parts.append(str(item.get("text")))
                    elif item.get("type") == "image_url":
                        image_url = item.get("image_url", {}) or {}
                        if image_url.get("url"):
                            parts.append(f"[image] {image_url['url']}")
                    elif item.get("content") is not None:
                        parts.append(str(item.get("content")))
                    else:
                        parts.append(json.dumps(item, ensure_ascii=False))
                else:
                    parts.append(str(item))
            return "\n".join(part for part in parts if part)
        if isinstance(content, dict):
            return json.dumps(content, ensure_ascii=False)
        return str(content)

    def _prepare_response_input(
        self,
        messages: List[Dict[str, Any]]
    ) -> tuple[Optional[str], List[Dict[str, Any]]]:
        instructions: List[str] = []
        conversation: List[Dict[str, Any]] = []

        for message in messages:
            role = message.get("role", "user")
            content = message.get("content")
            if role == "system":
                instruction_text = self._flatten_message_content(content)
                if instruction_text:
                    instructions.append(instruction_text)
                continue

            if isinstance(content, list):
                response_content = []
                for item in content:
                    if not isinstance(item, dict):
                        response_content.append({
                            "type": "input_text",
                            "text": str(item)
                        })
                        continue

                    item_type = item.get("type")
                    if item_type == "text":
                        response_content.append({
                            "type": "input_text",
                            "text": str(item.get("text", ""))
                        })
                    elif item_type == "image_url":
                        image_url = item.get("image_url", {}) or {}
                        url = image_url.get("url")
                        if url:
                            response_content.append({
                                "type": "input_image",
                                "image_url": url
                            })
                    else:
                        flattened = self._flatten_message_content(item)
                        if flattened:
                            response_content.append({
                                "type": "input_text",
                                "text": flattened
                            })
                if response_content:
                    conversation.append({
                        "role": role,
                        "content": response_content
                    })
                continue

            text_content = self._flatten_message_content(content)
            if text_content:
                conversation.append({
                    "role": role,
                    "content": [{
                        "type": "input_text",
                        "text": text_content
                    }]
                })

        instruction_text = "\n\n".join(instructions) if instructions else None
        return instruction_text, conversation

    def _build_response_payload(self, messages: List[Dict[str, Any]], stream: bool) -> Dict[str, Any]:
        instructions, input_items = self._prepare_response_input(messages)
        payload: Dict[str, Any] = {
            "model": self.model,
            "input": input_items,
            "stream": stream,
            # Disable server-side response storage. We never use
            # `previous_response_id`, so storing each response wastes
            # quota and may surface in unrelated dashboards.
            "store": False,
        }
        if instructions:
            payload["instructions"] = instructions
        if self.max_output_tokens is not None:
            payload["max_output_tokens"] = self.max_output_tokens
        if self.temperature is not None:
            payload["temperature"] = self.temperature
        if self.top_p is not None:
            payload["top_p"] = self.top_p
        return payload

    def _build_chat_payload(self,
                            messages: List[Dict[str, Any]],
                            stream: bool,
                            tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
        }
        if self.max_output_tokens is not None:
            payload["max_tokens"] = self.max_output_tokens
        if self.temperature is not None:
            payload["temperature"] = self.temperature
        if self.top_p is not None:
            payload["top_p"] = self.top_p
        if self.presence_penalty is not None:
            payload["presence_penalty"] = self.presence_penalty
        if self.frequency_penalty is not None:
            payload["frequency_penalty"] = self.frequency_penalty
        if self.stop is not None:
            payload["stop"] = self.stop
        if stream:
            payload["stream_options"] = {"include_usage": True}
        if tools:
            payload["tools"] = tools
        return payload

    def _extract_response_text(self, response: Dict[str, Any]) -> str:
        output_text = response.get("output_text")
        if output_text:
            return str(output_text)

        texts: List[str] = []
        for output in response.get("output", []) or []:
            if output.get("type") not in ("message", "", None):
                continue
            for item in output.get("content", []) or []:
                text_value = item.get("text")
                if isinstance(text_value, dict):
                    text_value = text_value.get("value")
                if text_value:
                    texts.append(str(text_value))
        return "".join(texts)

    def _create_response(self,
                         messages: List[Dict[str, Any]],
                         is_stream: bool,
                         track_history: bool = False) -> Union[str, Iterator[str]]:
        payload = self._build_response_payload(messages, stream=is_stream)
        if is_stream:
            return self._stream_response(payload, track_history)

        response = self._request_json("responses", payload)
        self._update_stats(response.get("usage"))
        response_text = self._extract_response_text(response)
        if track_history:
            self.history.append({"role": "assistant", "content": response_text})
        return response_text

    def _stream_response(self,
                         payload: Dict[str, Any],
                         track_history: bool = False) -> Iterator[str]:
        def generator() -> Iterator[str]:
            chunks: List[str] = []
            final_usage: Optional[Dict[str, Any]] = None

            for event in self._stream_json_lines("responses", payload):
                event_type = event.get("type")
                if event_type == "response.output_text.delta":
                    delta = event.get("delta")
                    if isinstance(delta, str) and delta:
                        chunks.append(delta)
                        yield delta
                elif event_type == "response.completed":
                    final_usage = (event.get("response") or {}).get("usage")

            self._update_stats(final_usage)
            final_text = "".join(chunks)
            if track_history:
                self.history.append({"role": "assistant", "content": final_text})

        return generator()

    def _create_chat_completion(self,
                                messages: List[Dict[str, Any]],
                                is_stream: bool,
                                tools: Optional[List[Dict[str, Any]]] = None,
                                raw_response: bool = False) -> Union[str, Iterator[Dict[str, Any]], Dict[str, Any]]:
        payload = self._build_chat_payload(messages, stream=is_stream, tools=tools)
        if is_stream:
            stream = self._stream_json_lines("chat/completions", payload)
            return stream if raw_response else self._process_stream(stream)

        response = self._request_json("chat/completions", payload)
        if raw_response:
            return response
        self._update_stats(response.get("usage"))
        choices = response.get("choices") or []
        if not choices:
            return ""
        return choices[0].get("message", {}).get("content", "") or ""

    def _process_tool_response(self,
                               response: Dict[str, Any],
                               tools: List[Dict[str, Any]],
                               function_module: Any) -> str:
        choices = response.get("choices") or []
        self._update_stats(response.get("usage"))
        if not choices:
            return ""

        assistant_output = choices[0].get("message", {})
        tool_calls = assistant_output.get("tool_calls") or []
        if tool_calls:
            self.history.append({
                "role": "assistant",
                "content": assistant_output.get("content"),
                "tool_calls": tool_calls
            })
            tool_outputs = self._execute_tool_calls(tool_calls, function_module)
            self.history.extend(tool_outputs)
            second_response = self._create_chat_completion(
                self.history,
                is_stream=False,
                tools=tools,
                raw_response=True
            )
            self._update_stats(second_response.get("usage"))
            second_choices = second_response.get("choices") or []
            final_output = ""
            if second_choices:
                final_output = second_choices[0].get("message", {}).get("content", "") or ""
            self.history.append({"role": "assistant", "content": final_output})
            return final_output

        final_output = assistant_output.get("content", "") or ""
        self.history.append({"role": "assistant", "content": final_output})
        return final_output

    def _unified_tool_stream(self,
                             messages: List[Dict[str, Any]],
                             tools: List[Dict[str, Any]],
                             function_module: Any) -> Iterator[str]:
        def generator() -> Iterator[str]:
            full_response = ""
            tool_calls: List[Dict[str, Any]] = []
            final_usage: Optional[Dict[str, Any]] = None

            try:
                stream = self._create_chat_completion(
                    messages,
                    is_stream=True,
                    tools=tools,
                    raw_response=True
                )
                for chunk in stream:
                    choices = chunk.get("choices") or []
                    if chunk.get("usage") is not None:
                        final_usage = chunk.get("usage")
                    if not choices:
                        continue
                    delta = choices[0].get("delta", {})
                    content = delta.get("content")
                    if content:
                        full_response += content
                        yield content
                    for tool_call in delta.get("tool_calls", []) or []:
                        index = tool_call.get("index", 0)
                        while len(tool_calls) <= index:
                            tool_calls.append({
                                "id": "",
                                "type": "function",
                                "function": {"name": "", "arguments": ""}
                            })
                        existing = tool_calls[index]
                        if tool_call.get("id"):
                            existing["id"] = tool_call["id"]
                        function_info = tool_call.get("function", {}) or {}
                        if function_info.get("name"):
                            existing["function"]["name"] = function_info["name"]
                        if function_info.get("arguments"):
                            existing["function"]["arguments"] += function_info["arguments"]

                self._update_stats(final_usage)

                if tool_calls:
                    tool_outputs = self._execute_tool_calls(tool_calls, function_module)
                    self.history.append({"role": "assistant", "content": full_response, "tool_calls": tool_calls})
                    self.history.extend(tool_outputs)
                    for tool_output in tool_outputs:
                        yield f"Tool {tool_output['tool_call_id']} returned result: {tool_output['content']}\n"

                    second_response = self._create_chat_completion(
                        self.history,
                        is_stream=False,
                        tools=tools,
                        raw_response=True
                    )
                    self._update_stats(second_response.get("usage"))
                    second_choices = second_response.get("choices") or []
                    final_output = ""
                    if second_choices:
                        final_output = second_choices[0].get("message", {}).get("content", "") or ""
                    self.history.append({"role": "assistant", "content": final_output})
                    if final_output:
                        yield final_output
                else:
                    self.history.append({"role": "assistant", "content": full_response})
                    if full_response.strip():
                        yield f"\n{full_response}\n"
                    else:
                        yield "\nUnable to generate a response. Please try again.\n"
            except Exception as exc:
                yield f"An error occurred: {str(exc)}"

            self.history = [
                msg for msg in self.history[-5:]
                if self._flatten_message_content(msg.get("content", "")).strip()
            ]

        return generator()

    def _process_stream(self, stream: Iterator[Dict[str, Any]]) -> Iterator[str]:
        def generator() -> Iterator[str]:
            full_response = ""
            final_usage: Optional[Dict[str, Any]] = None
            for chunk in stream:
                if chunk.get("usage") is not None:
                    final_usage = chunk.get("usage")
                choices = chunk.get("choices") or []
                if not choices:
                    continue
                content = (choices[0].get("delta", {}) or {}).get("content")
                if content:
                    full_response += content
                    yield content
            self._update_stats(final_usage)
            self.history.append({"role": "assistant", "content": full_response})

        return generator()

    def _execute_tool_calls(self,
                            tool_calls: List[Dict[str, Any]],
                            function_module: Any) -> List[Dict[str, str]]:
        tool_outputs: List[Dict[str, str]] = []
        for tool_call in tool_calls:
            function_info = tool_call.get("function", {}) or {}
            tool_name = function_info.get("name", "")
            raw_arguments = function_info.get("arguments", "")
            tool_call_id = tool_call.get("id", "")
            try:
                tool_args = json.loads(raw_arguments) if raw_arguments else {}
            except json.JSONDecodeError:
                tool_args = {}

            if hasattr(function_module, tool_name):
                tool_func = getattr(function_module, tool_name)
                try:
                    tool_output = tool_func(**tool_args)
                    content = str(tool_output)
                except Exception as exc:
                    content = f"Error executing {tool_name}: {str(exc)}"
            else:
                content = f"Error: Function {tool_name} not found."

            tool_outputs.append({
                "role": "tool",
                "name": tool_name,
                "content": content,
                "tool_call_id": tool_call_id
            })
        return tool_outputs

    def _encode_image_to_base64(self, image_path: str) -> str:
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode("utf-8")
            return f"data:image/jpeg;base64,{base64_image}"

    def _update_stats(self, usage: Optional[Dict[str, Any]]) -> None:
        self.chat_count += 1
        if usage is None:
            return

        prompt_tokens = usage.get("prompt_tokens")
        completion_tokens = usage.get("completion_tokens")
        total_tokens = usage.get("total_tokens")

        if prompt_tokens is None:
            prompt_tokens = usage.get("input_tokens", 0)
        if completion_tokens is None:
            completion_tokens = usage.get("output_tokens", 0)
        if total_tokens is None:
            total_tokens = (prompt_tokens or 0) + (completion_tokens or 0)

        self.prompt_token_count += int(prompt_tokens or 0)
        self.completion_token_count += int(completion_tokens or 0)
        self.token_count += int(total_tokens or 0)
