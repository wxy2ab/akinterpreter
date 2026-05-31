from typing import Iterator, List, Dict, Any, Optional, Union
from openai import OpenAI
import json
import httpx
from ._llm_api_client import LLMApiClient
from ..utils.config_setting import Config
from ..utils.handle_max_tokens import handle_max_tokens
from ratelimit import limits, sleep_and_retry
from tenacity import retry, stop_after_attempt, wait_fixed


class MoonShotClient(LLMApiClient):
    supports_structured_output = True

    def __init__(self, api_key: str = "", base_url: str = "https://api.moonshot.cn/v1",
                 max_tokens: Optional[int] = None, temperature: float = 1, top_p: Optional[float] = None,
                 presence_penalty: Optional[float] = 0, frequency_penalty: Optional[float] = 0, stop: Optional[Union[str, List[str]]] = None,
                 enable_thinking: Optional[bool] = None
                 ):
        config = Config()
        if api_key == "" and config.has_key("moonshot_api_key"):
            api_key = config.get("moonshot_api_key")
            
        http_client = httpx.Client(
            limits=httpx.Limits(max_keepalive_connections=100, max_connections=200),
            timeout=httpx.Timeout(timeout=600.0, connect=60.0, read=600.0, write=120.0)
        )
            
        self.client = OpenAI(
            api_key=api_key, 
            base_url=base_url,
            http_client=http_client,
            max_retries=5
        )
        self.chat_count = 0
        self.token_count = 0
        self.prompt_token_count = 0
        self.completion_token_count = 0
        self.history = []
        self._model_list = ["moonshot-v1-128k", "moonshot-v1-8k", "moonshot-v1-32k"]
        self.model = self._model_list[0]
        self.temperature = temperature
        self.top_p = top_p
        self.presence_penalty = presence_penalty
        self.frequency_penalty = frequency_penalty
        self.stop = stop
        self.enable_thinking = enable_thinking
        self._response_format: Optional[Dict[str, Any]] = None

    def set_system_message(self, system_message: str = "你是一个智能助手,擅长把复杂问题清晰明白通俗易懂地解答出来"):
        self.history = [{"role": "system", "content": system_message}]

    def set_response_format(self, fmt: Optional[Dict[str, Any]]) -> None:
        if fmt is not None and not isinstance(fmt, dict):
            raise TypeError("response_format must be a dict or None")
        self._response_format = fmt

    @handle_max_tokens
    def text_chat(self, message: str, is_stream: bool = False) -> Union[str, Iterator[str]]:
        if not self.history:
            self.set_system_message()
        self.history.append({"role": "user", "content": message})
        return self._create_chat_completion(self.history, is_stream)

    @sleep_and_retry
    @limits(calls=20, period=1)
    @retry(stop=stop_after_attempt(12), wait=wait_fixed(5))
    def one_chat(self, message: str, is_stream: bool = False) -> Union[str, Iterator[str]]:
        if not self.history:
            self.set_system_message()
        msg = [{"role": "user", "content": message}] if isinstance(message, str) else message
        return self._create_chat_completion(msg, is_stream)

    def tool_chat(self, user_message: str, tools: List[Dict[str, Any]], function_module: Any, is_stream: bool = False) -> Union[str, Iterator[str]]:
        if not self.history:
            self.set_system_message()
        self.history.append({"role": "user", "content": user_message})
        if is_stream:
            return self._unified_tool_stream(self.history, tools, function_module)
        else:
            response = self._create_chat_completion(self.history, is_stream, tools)
            return self._process_tool_response(response, tools, function_module)

    def _unified_tool_stream(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]], function_module: Any) -> Iterator[str]:
        try:
            response_stream = self._create_chat_completion(messages, True, tools, raw_response=True)
            full_response = ""
            tool_calls = []

            for chunk in response_stream:
                if isinstance(chunk, str):
                    content = chunk
                elif hasattr(chunk, 'choices') and chunk.choices:
                    delta = chunk.choices[0].delta
                    content = delta.content if hasattr(delta, 'content') and delta.content is not None else None
                    if hasattr(delta, 'tool_calls') and delta.tool_calls:
                        for tool_call in delta.tool_calls:
                            if tool_call.index >= len(tool_calls):
                                tool_calls.append({
                                    "id": tool_call.id,
                                    "type": "function",
                                    "function": {"name": tool_call.function.name, "arguments": tool_call.function.arguments or ""}
                                })
                            else:
                                tool_calls[tool_call.index]["function"]["arguments"] += tool_call.function.arguments or ""
                if content:
                    yield content
                    full_response += content

            if tool_calls:
                tool_outputs = self._execute_tool_calls(tool_calls, function_module)
                tool_results = []
                for tool_output in tool_outputs:
                    result = f"工具 {tool_output['tool_call_id']} 返回结果: {tool_output['content']}"
                    tool_results.append(result)
                    yield result + "\n"
                
                tool_result_message = "\n".join(tool_results)
                messages.append({"role": "assistant", "content": f"{full_response}\n\n工具调用结果:\n{tool_result_message}"})
                
                explanation_request = "请解释上述工具调用的结果，并提供一个简洁明了的回答。"
                messages.append({"role": "user", "content": explanation_request})
                
                explanation_stream = self._create_chat_completion(messages, True, tools, raw_response=True)
                for chunk in explanation_stream:
                    if isinstance(chunk, str):
                        yield chunk
                    elif hasattr(chunk, 'choices') and chunk.choices:
                        delta = chunk.choices[0].delta
                        content = delta.content if hasattr(delta, 'content') and delta.content is not None else None
                        if content:
                            yield content
            elif full_response.strip():
                yield f"\n{full_response}\n"
            else:
                yield "\n无法生成回答。请尝试重新提问。\n"
        except Exception as e:
            yield f"发生错误: {str(e)}"

        self.history = [msg for msg in messages[-5:] if msg.get('content', '').strip()]

    def _create_chat_completion(self, messages: List[Dict[str, str]], is_stream: bool, tools: List[Dict[str, Any]] = None, raw_response: bool = False) -> Union[str, Iterator[str]]:
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "stream": is_stream,
            "timeout": 600,
        }
        if is_stream:
            kwargs["stream_options"] = {"include_usage": True}
        
        # 构建 extra_body
        extra_body = {}
        if self.enable_thinking is not None:
            extra_body["enable_thinking"] = self.enable_thinking
        
        if extra_body:
            kwargs["extra_body"] = extra_body
            
        if self.top_p is not None:
            kwargs["top_p"] = self.top_p
        if self.presence_penalty is not None:
            kwargs["presence_penalty"] = self.presence_penalty
        if self.frequency_penalty is not None:
            kwargs["frequency_penalty"] = self.frequency_penalty
        if self.stop is not None:
            kwargs["stop"] = self.stop
        if tools:
            kwargs["tools"] = tools
        # Skip JSON mode when tools are present: OpenAI-compatible APIs treat
        # the tools + response_format={"type":"json_object"} combination as
        # ambiguous (tool_calls may not respect the JSON envelope; structured
        # outputs can conflict with tool schemas). See
        # core/ccx/docs/role_based_llm_routing.md §7.
        if self._response_format and not tools:
            kwargs["response_format"] = self._response_format

        completion = self.client.chat.completions.create(**kwargs)
        if is_stream:
            return completion if raw_response else self._process_stream(completion)
        else:
            if raw_response:
                return completion
            if not completion.choices:
                raise RuntimeError("LLM API returned empty choices")
            response = completion.choices[0].message.content
            self._update_stats(completion.usage)
            return response

    def tool_invoke(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "stream": False,
            "timeout": 600,
            "tools": tools,
        }
        extra_body = {}
        if self.enable_thinking is not None:
            extra_body["enable_thinking"] = self.enable_thinking
        if extra_body:
            kwargs["extra_body"] = extra_body
        if self.top_p is not None:
            kwargs["top_p"] = self.top_p
        if self.presence_penalty is not None:
            kwargs["presence_penalty"] = self.presence_penalty
        if self.frequency_penalty is not None:
            kwargs["frequency_penalty"] = self.frequency_penalty
        if self.stop is not None:
            kwargs["stop"] = self.stop
        # No response_format on tool paths — see _create_chat_completion gate
        # for rationale.

        completion = self.client.chat.completions.create(**kwargs)
        self._update_stats(completion.usage)
        if not completion.choices:
            return self._normalize_tool_invoke_response("", None)
        message = completion.choices[0].message
        return self._normalize_tool_invoke_response(
            getattr(message, "content", "") or "",
            getattr(message, "tool_calls", None)
        )

    def _process_tool_response(self, response, tools: List[Dict[str, Any]], function_module: Any) -> str:
        if not response.choices:
            return ""
        assistant_output = response.choices[0].message
        self._update_stats(response.usage)

        if hasattr(assistant_output, 'tool_calls') and assistant_output.tool_calls:
            self.history.append({"role": "assistant", "content": assistant_output.content, "tool_calls": assistant_output.tool_calls})
            tool_outputs = self._execute_tool_calls(assistant_output.tool_calls, function_module)
            self.history.extend(tool_outputs)
            second_response = self._create_chat_completion(self.history, False, tools, raw_response=True)
            if not second_response.choices:
                final_output = ""
            else:
                self._update_stats(second_response.usage)
                final_output = second_response.choices[0].message.content or ""
        else:
            self.history.append({"role": "assistant", "content": assistant_output.content})
            final_output = assistant_output.content

        return final_output

    def _process_stream(self, stream) -> Iterator[str]:
        full_response = ""
        usage_updated = False
        for chunk in stream:
            usage = getattr(chunk, 'usage', None)
            if usage is not None:
                self._update_stats(usage)
                usage_updated = True
            if hasattr(chunk, 'choices') and chunk.choices:
                delta = chunk.choices[0].delta
                if hasattr(delta, 'content') and delta.content:
                    full_response += delta.content
                    yield delta.content
        if not usage_updated:
            self._update_stats(None)
        self.history.append({"role": "assistant", "content": full_response})

    def _execute_tool_calls(self, tool_calls, function_module: Any) -> List[Dict[str, str]]:
        tool_outputs = []
        for tool_call in tool_calls:
            tc_function = getattr(tool_call, "function", None) or (tool_call.get("function") if isinstance(tool_call, dict) else None)
            tool_name = getattr(tc_function, "name", None) or (tc_function.get("name", "") if isinstance(tc_function, dict) else "")
            raw_args = getattr(tc_function, "arguments", None) or (tc_function.get("arguments", "{}") if isinstance(tc_function, dict) else "{}")
            tc_id = getattr(tool_call, "id", None) or (tool_call.get("id", "") if isinstance(tool_call, dict) else "")
            try:
                tool_args = json.loads(raw_args) if isinstance(raw_args, str) else dict(raw_args or {})
            except (json.JSONDecodeError, TypeError):
                tool_args = {}

            if hasattr(function_module, tool_name):
                tool_func = getattr(function_module, tool_name)
                try:
                    tool_output = tool_func(**tool_args)
                    tool_outputs.append({
                        "role": "tool",
                        "content": str(tool_output),
                        "tool_call_id": tc_id,
                    })
                except Exception as e:
                    tool_outputs.append({
                        "role": "tool",
                        "content": f"Error executing {tool_name}: {str(e)}",
                        "tool_call_id": tc_id,
                    })
            else:
                tool_outputs.append({
                    "role": "tool",
                    "content": f"Error: Function {tool_name} not found.",
                    "tool_call_id": tc_id,
                })

        return tool_outputs

    def _extract_usage_counts(self, usage: Any) -> Dict[str, int]:
        normalized_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }
        if usage is None:
            return normalized_usage

        if hasattr(usage, "model_dump"):
            usage = usage.model_dump()
        elif not isinstance(usage, dict):
            usage = {
                "prompt_tokens": getattr(usage, "prompt_tokens", 0),
                "completion_tokens": getattr(usage, "completion_tokens", 0),
                "total_tokens": getattr(usage, "total_tokens", 0),
            }

        for key in normalized_usage:
            value = usage.get(key, 0) if isinstance(usage, dict) else 0
            try:
                normalized_usage[key] = int(value or 0)
            except (TypeError, ValueError):
                normalized_usage[key] = 0

        if normalized_usage["total_tokens"] == 0:
            normalized_usage["total_tokens"] = (
                normalized_usage["prompt_tokens"] +
                normalized_usage["completion_tokens"]
            )

        return normalized_usage

    def _update_stats(self, usage: Any):
        self.chat_count += 1
        usage_counts = self._extract_usage_counts(usage)
        self.prompt_token_count += usage_counts["prompt_tokens"]
        self.completion_token_count += usage_counts["completion_tokens"]
        self.token_count += usage_counts["total_tokens"]

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_chats": self.chat_count,
            "total_tokens": self.token_count,
            "prompt_tokens": self.prompt_token_count,
            "completion_tokens": self.completion_token_count,
        }

    def clear_chat(self) -> None:
        self.history = []

    def image_chat(self, message: str, image_path: str) -> str:
        raise NotImplementedError("MoonShot API does not support image chat.")

    def audio_chat(self, message: str, audio_path: str) -> str:
        raise NotImplementedError("MoonShot API does not support audio chat.")

    def video_chat(self, message: str, video_path: str) -> str:
        raise NotImplementedError("MoonShot API does not support video chat.")
