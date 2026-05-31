import base64
import json
import mimetypes
from typing import List, Dict, Any, Literal, Optional, Union, Iterator

import requests
from tenacity import retry, stop_after_attempt, wait_fixed

from ._llm_api_client import LLMApiClient
from ..utils.config_setting import Config
from ..utils.handle_max_tokens import handle_max_tokens

class GLMClient(LLMApiClient):
    def __init__(self, api_key: str = "", model: Literal["glm-4-plus","glm-5", "glm-5.1", "glm-4-air", "glm-4-airx", "glm-4-long","glm-4-flashx" ,"glm-4-flash"] = "glm-5.1",
                 do_sample: bool = False, temperature: float = 1, top_p: float = 0.7, max_tokens: Optional[int] = None, stop: Union[str, List[str], None] = None,
                 thinking: bool = False):
        config = Config()
        if api_key == "" and config.has_key("glm_api_key"):
            api_key = config.get("glm_api_key")
        self.api_key = api_key
        self.base_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        self.timeout = 600
        self.model = model
        self.history = []
        self.do_sample = do_sample
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        self.stop = stop
        self.thinking = thinking

    def set_system_message(self, system_message: str = "你是一个智能助手,擅长把复杂问题清晰明白通俗易懂地解答出来"):
        self.history = [{"role": "system", "content": system_message}]

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    def _build_payload(
        self,
        messages: List[Dict[str, Any]],
        stream: bool = False,
        tools: Union[List[Dict[str, Any]], None] = None,
        tool_choice: Union[str, Dict[str, Any], None] = None
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "do_sample": self.do_sample,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
            "stream": stream,
            "thinking": {
                "type": "enabled" if self.thinking else "disabled"
            }
        }
        if self.stop is not None:
            payload["stop"] = self.stop
        if tools is not None:
            payload["tools"] = tools
        if tool_choice is not None:
            payload["tool_choice"] = tool_choice
        return payload

    def _make_request(self, payload: Dict[str, Any], stream: bool = False) -> Union[Dict[str, Any], Iterator[Dict[str, Any]]]:
        response = requests.post(
            self.base_url,
            headers=self._get_headers(),
            json=payload,
            stream=stream,
            timeout=self.timeout
        )
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            error_text = response.text.strip()
            raise requests.HTTPError(f"{exc} - {error_text}") from exc

        if stream:
            return self._parse_stream_response(response)
        return response.json()

    def _parse_stream_response(self, response: requests.Response) -> Iterator[Dict[str, Any]]:
        for raw_line in response.iter_lines(decode_unicode=True):
            if not raw_line:
                continue
            line = raw_line.strip()
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            try:
                yield json.loads(data)
            except json.JSONDecodeError:
                continue

    def _message_content_to_text(self, content: Any) -> str:
        if content is None:
            return ""
        if isinstance(content, str):
            return content
        if isinstance(content, dict):
            for key in ("text", "content", "output_text", "reasoning_content"):
                if key in content:
                    text = self._message_content_to_text(content.get(key))
                    if text.strip():
                        return text
            return json.dumps(content, ensure_ascii=False)
        if isinstance(content, list):
            text_parts: List[str] = []
            for part in content:
                text = self._message_content_to_text(part)
                if text.strip():
                    text_parts.append(text)
            return "\n".join(text_parts)
        return str(content)

    def _extract_message(self, response: Dict[str, Any]) -> Dict[str, Any]:
        choices = response.get("choices") or []
        if not choices:
            return {}
        return choices[0].get("message") or {}

    def _extract_delta(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        choices = chunk.get("choices") or []
        if not choices:
            return {}
        return choices[0].get("delta") or {}

    def _extract_content(self, response: Dict[str, Any]) -> str:
        message = self._extract_message(response)
        content = self._message_content_to_text(message.get("content"))
        if content.strip():
            return content
        reasoning_content = self._message_content_to_text(message.get("reasoning_content"))
        if reasoning_content.strip():
            return reasoning_content
        return ""

    def _resolve_stream_flag(self, is_stream: bool, kwargs: Dict[str, Any]) -> bool:
        if "stream" in kwargs:
            is_stream = bool(kwargs.pop("stream"))
        if kwargs:
            unexpected = ", ".join(sorted(kwargs.keys()))
            raise TypeError(f"Unexpected keyword argument(s): {unexpected}")
        return is_stream

    def _append_tool_call_chunk(self, tool_calls: List[Dict[str, Any]], tool_call: Dict[str, Any]) -> None:
        index = tool_call.get("index", len(tool_calls))
        while len(tool_calls) <= index:
            tool_calls.append({
                "id": "",
                "type": "function",
                "function": {
                    "name": "",
                    "arguments": ""
                }
            })

        current = tool_calls[index]
        if tool_call.get("id"):
            current["id"] = tool_call["id"]
        if tool_call.get("type"):
            current["type"] = tool_call["type"]

        function_data = tool_call.get("function") or {}
        if function_data.get("name"):
            current["function"]["name"] = function_data["name"]
        if function_data.get("arguments"):
            current["function"]["arguments"] += function_data["arguments"]

    def _extract_tool_calls(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        message = self._extract_message(response)
        tool_calls = []
        for tool_call in message.get("tool_calls") or []:
            function_data = tool_call.get("function") or {}
            tool_calls.append({
                "id": tool_call.get("id", ""),
                "type": tool_call.get("type", "function"),
                "function": {
                    "name": function_data.get("name", ""),
                    "arguments": function_data.get("arguments", "")
                }
            })
        return tool_calls

    def _stream_text_response(self, stream: Iterator[Dict[str, Any]], persist_history: bool) -> Iterator[str]:
        full_response = ""
        for chunk in stream:
            delta = self._extract_delta(chunk)
            content = delta.get("content")
            if content:
                full_response += content
                yield content
        if persist_history:
            self.history.append({"role": "assistant", "content": full_response})

    def _safe_load_tool_arguments(self, arguments: str) -> Dict[str, Any]:
        if not arguments:
            return {}
        try:
            loaded = json.loads(arguments)
        except json.JSONDecodeError:
            return {"raw_input": arguments}
        return loaded if isinstance(loaded, dict) else {"raw_input": loaded}

    def _execute_tool_call(self, tool_call: Dict[str, Any], function_module: Any) -> Dict[str, Any]:
        tool_name = tool_call["function"]["name"]
        tool_args = self._safe_load_tool_arguments(tool_call["function"]["arguments"])

        if hasattr(function_module, tool_name):
            tool_func = getattr(function_module, tool_name)
            try:
                tool_output = tool_func(**tool_args)
                return {"success": True, "content": str(tool_output), "tool_name": tool_name}
            except Exception as e:
                return {"success": False, "content": f"Error executing {tool_name}: {str(e)}", "tool_name": tool_name}
        return {"success": False, "content": f"Function {tool_name} not found in the provided module.", "tool_name": tool_name}

    @handle_max_tokens
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(10))
    def text_chat(self, message: str, is_stream: bool = False, **kwargs) -> Union[str, Iterator[str]]:
        is_stream = self._resolve_stream_flag(is_stream, kwargs)
        if not self.history:
            self.set_system_message()
        self.history.append({"role": "user", "content": message})

        payload = self._build_payload(self.history, stream=is_stream)
        if is_stream:
            response = self._make_request(payload, stream=True)
            return self._stream_text_response(response, persist_history=True)

        response = self._make_request(payload)
        output = self._extract_content(response)
        self.history.append({"role": "assistant", "content": output})
        return output

    def one_chat(self, message: Union[str, List[Union[str, Dict[str, str]]]], is_stream: bool = False, **kwargs) -> Union[str, Iterator[str]]:
        is_stream = self._resolve_stream_flag(is_stream, kwargs)
        if isinstance(message, str):
            messages = [{"role": "user", "content": message}]
        elif isinstance(message, list):
            messages = []
            for msg in message:
                if isinstance(msg, str):
                    messages.append({"role": "user", "content": msg})
                elif isinstance(msg, dict) and "role" in msg and "content" in msg:
                    messages.append(msg)
                else:
                    raise ValueError("Invalid message format in list")
        else:
            raise ValueError("Invalid input type for message")

        payload = self._build_payload(messages, stream=is_stream)
        if is_stream:
            response = self._make_request(payload, stream=True)
            return self._stream_text_response(response, persist_history=False)
        response = self._make_request(payload)
        return self._extract_content(response)

    def tool_chat(self, user_message: str, tools: List[Dict[str, Any]], function_module: Any = None, is_stream: bool = False, **kwargs) -> Union[str, Iterator[str]]:
        is_stream = self._resolve_stream_flag(is_stream, kwargs)
        if not self.history:
            self.set_system_message()
        self.history.append({"role": "user", "content": user_message})

        payload = self._build_payload(self.history, stream=is_stream, tools=tools, tool_choice="auto")
        if is_stream:
            response = self._make_request(payload, stream=True)
            return self._stream_tool_chat(response, function_module)
        response = self._make_request(payload)
        return self._non_stream_tool_chat(response, function_module)

    def _stream_tool_chat(self, response: Iterator[Dict[str, Any]], function_module: Any) -> Iterator[str]:
        full_response = ""
        tool_calls = []

        for chunk in response:
            delta = self._extract_delta(chunk)
            content = delta.get("content")
            if content is not None:
                yield content
                full_response += content

            for tool_call in delta.get("tool_calls") or []:
                self._append_tool_call_chunk(tool_calls, tool_call)

        if tool_calls:
            if not full_response:
                full_response = f"我将调用工具:{tool_calls[0]['function']['name']}"
            assistant_message = {
                "role": "assistant",
                "content": full_response,
                "tool_calls": tool_calls
            }
            self.history.append(assistant_message)

            yield "\n执行工具调用...\n"
            for tool_call in tool_calls:
                execution_result = self._execute_tool_call(tool_call, function_module)
                if execution_result["success"]:
                    yield f"工具 {tool_call['id']} 返回结果: {execution_result['content']}\n"
                else:
                    yield f"工具 {tool_call['id']} 执行错误: {execution_result['content']}\n"
                tool_msg = {
                    "role": "tool",
                    "content": execution_result["content"],
                    "tool_call_id": tool_call["id"]
                }
                self.history.append(tool_msg)

            yield "\n生成最终回复...\n"
            final_response = self._make_request(self._build_payload(self.history, stream=True), stream=True)
            final_output = ""
            for chunk in final_response:
                delta = self._extract_delta(chunk)
                content = delta.get("content")
                if content:
                    final_output += content
                    yield content
            self.history.append({"role": "assistant", "content": final_output})
        else:
            self.history.append({"role": "assistant", "content": full_response})

    def _non_stream_tool_chat(self, response: Dict[str, Any], function_module: Any) -> str:
        message = self._extract_message(response)
        full_response = self._message_content_to_text(message.get("content"))
        tool_calls = self._extract_tool_calls(response)
        assistant_message = {
            "role": "assistant",
            "content": full_response,
            "tool_calls": tool_calls
        }
        self.history.append(assistant_message)

        if tool_calls:
            for tool_call in tool_calls:
                execution_result = self._execute_tool_call(tool_call, function_module)
                tool_msg = {"role": "tool", "content": execution_result["content"], "tool_call_id": tool_call["id"]}
                self.history.append(tool_msg)

            final_response = self._make_request(self._build_payload(self.history))
            final_output = self._extract_content(final_response)
            self.history.append({"role": "assistant", "content": final_output})
            return final_output
        return full_response
        
    def _execute_tool_calls(self, tool_calls, function_module):
        tool_outputs = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            if hasattr(function_module, tool_name):
                tool_func = getattr(function_module, tool_name)
                tool_args = json.loads(tool_call.function.arguments)
                tool_output = tool_func(**tool_args)
                tool_outputs.append({
                    "role": "tool",
                    "content": json.dumps(tool_output),
                    "tool_call_id": tool_call.id
                })
            else:
                error_msg = f"Function {tool_name} not found in the provided module."
                tool_outputs.append({
                    "role": "tool",
                    "content": error_msg,
                    "tool_call_id": tool_call.id
                })
        return tool_outputs

    def tool_invoke(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        response = self._make_request(
            self._build_payload(messages, stream=False, tools=tools, tool_choice="auto")
        )
        message = self._extract_message(response)
        return self._normalize_tool_invoke_response(
            message.get("content", "") or "",
            message.get("tool_calls", None)
        )

    def clear_chat(self) -> None:
        self.history = []

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_messages": len(self.history)
        }

    def _process_image(self, image_path: str) -> str:
        if image_path.startswith(('http://', 'https://')):
            return image_path
        mime_type = mimetypes.guess_type(image_path)[0] or "image/jpeg"
        with open(image_path, 'rb') as img_file:
            encoded = base64.b64encode(img_file.read()).decode('utf-8')
        return f"data:{mime_type};base64,{encoded}"

    def image_chat(self, message: str, image_paths: Union[str, List[str]], is_stream: bool = False, **kwargs) -> Union[str, Iterator[str]]:
        is_stream = self._resolve_stream_flag(is_stream, kwargs)
        if isinstance(image_paths, str):
            image_paths = [image_paths]
        
        image_contents = [{"type": "image_url", "image_url": {"url": self._process_image(path)}} for path in image_paths]
        image_contents.append({"type": "text", "text": message})
        
        messages = [{"role": "user", "content": image_contents}]

        payload = self._build_payload(messages, stream=is_stream)
        if is_stream:
            response = self._make_request(payload, stream=True)

            def generate():
                full_response = ""
                for chunk in response:
                    delta = self._extract_delta(chunk)
                    content = delta.get("content")
                    if content:
                        full_response += content
                        yield content
                self.history.append({"role": "user", "content": message})
                self.history.append({"role": "assistant", "content": full_response})

            return generate()

        response = self._make_request(payload)
        output = self._extract_content(response)
        self.history.append({"role": "user", "content": message})
        self.history.append({"role": "assistant", "content": output})
        return output

    def video_chat(self, message: str, video_path: str, is_stream: bool = False, **kwargs) -> Union[str, Iterator[str]]:
        is_stream = self._resolve_stream_flag(is_stream, kwargs)
        if not video_path.startswith(('http://', 'https://')):
            raise ValueError("Video chat only supports URL inputs. Please provide a valid video URL.")
        
        video_content = [
            {"type": "video_url", "video_url": {"url": video_path}},
            {"type": "text", "text": message}
        ]
        
        messages = [{"role": "user", "content": video_content}]

        payload = self._build_payload(messages, stream=is_stream)
        if is_stream:
            response = self._make_request(payload, stream=True)

            def generate():
                full_response = ""
                for chunk in response:
                    delta = self._extract_delta(chunk)
                    content = delta.get("content")
                    if content:
                        full_response += content
                        yield content
                self.history.append({"role": "user", "content": message})
                self.history.append({"role": "assistant", "content": full_response})

            return generate()

        response = self._make_request(payload)
        output = self._extract_content(response)
        self.history.append({"role": "user", "content": message})
        self.history.append({"role": "assistant", "content": output})
        return output

    def audio_chat(self, message: str, audio_path: str) -> str:
        raise NotImplementedError("GLM API does not support audio chat.")
