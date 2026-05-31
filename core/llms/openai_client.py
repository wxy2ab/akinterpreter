import json
import base64
import httpx
from typing import Union, List, Dict, Any, Iterator, Optional
from openai import OpenAI
from ._llm_api_client import LLMApiClient
from ..utils.config_setting import Config
from ..utils.handle_max_tokens import handle_max_tokens

class OpenAIClient(LLMApiClient):

    def __init__(self,
                 api_key: str = "",
                 model="gpt-5.4-mini",
                 base_url: str = "",
                 max_tokens: Optional[int] = None,
                 temperature: float = 0.3,
                 top_p: float = 1,
                 presence_penalty: float = 0,
                 frequency_penalty: float = 0,
                 stop: Union[str, List[str]] = None):
        config = Config()
        if api_key == "" and config.has_key("openai_api_key"):
            api_key = config.get("openai_api_key")
        self.api_key = api_key
        
        http_client = httpx.Client(
            limits=httpx.Limits(max_keepalive_connections=100, max_connections=200),
            timeout=httpx.Timeout(timeout=600.0, connect=60.0, read=600.0, write=120.0)
        )
        
        if base_url:
            self.base_url = base_url
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                http_client=http_client,
                max_retries=5
            )
        else:
            self.client = OpenAI(
                api_key=self.api_key,
                http_client=http_client,
                max_retries=5
            )
        self.chat_count = 0
        self.token_count = 0
        self.history = []
        self.model = model
        self.max_output_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.presence_penalty = presence_penalty
        self.frequency_penalty = frequency_penalty
        self.stop = stop
        self.wire_api = "responses"

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
                 message: str,
                 is_stream: bool = False) -> Union[str, Iterator[str]]:
        if not self.history:
            self.set_system_message()
        msg = [{
            "role": "user",
            "content": message
        }] if isinstance(message, str) else message
        return self._create_response(msg, is_stream, track_history=False)

    def tool_chat(self,
                  user_message: str,
                  tools: List[Dict[str, Any]],
                  function_module: Any,
                  is_stream: bool = False) -> Union[str, Iterator[str]]:
        if not self.history:
            self.set_system_message()
        self.history.append({"role": "user", "content": user_message})
        if is_stream:
            return self._unified_tool_stream(self.history, tools,
                                             function_module)
        else:
            response = self._create_chat_completion(self.history, is_stream,
                                                    tools, raw_response=True)
            return self._process_tool_response(response, tools,
                                               function_module)

    def image_chat(self,
                   message: str,
                   image_path_or_url: str,
                   is_stream: bool = False) -> Union[str, Iterator[str]]:
        if not self.history:
            self.set_system_message()

        if image_path_or_url.startswith(
                "http://") or image_path_or_url.startswith("https://"):
            image_content = {
                "type": "image_url",
                "image_url": {
                    "url": image_path_or_url
                }
            }
        else:
            image_content = {
                "type": "image_url",
                "image_url": {
                    "url": self._encode_image_to_base64(image_path_or_url)
                }
            }

        self.history.append({
            "role":
            "user",
            "content": [{
                "type": "text",
                "text": message
            }, image_content]
        })
        return self._create_response(self.history, is_stream, track_history=True)

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
        instructions = []
        conversation = []
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

                    if item.get("type") == "text":
                        response_content.append({
                            "type": "input_text",
                            "text": str(item.get("text", ""))
                        })
                    elif item.get("type") == "image_url":
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

    def _build_response_kwargs(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        instructions, input_items = self._prepare_response_input(messages)
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "input": input_items,
        }
        if self.max_output_tokens is not None:
            kwargs["max_output_tokens"] = self.max_output_tokens
        if self.temperature is not None:
            kwargs["temperature"] = self.temperature
        if self.top_p is not None:
            kwargs["top_p"] = self.top_p
        if instructions:
            kwargs["instructions"] = instructions
        return kwargs

    def _extract_response_text(self, response: Any) -> str:
        output_text = getattr(response, "output_text", None)
        if output_text:
            return output_text

        texts = []
        for output in getattr(response, "output", []) or []:
            output_type = getattr(output, "type", "")
            if output_type not in ("message", "", None):
                continue
            for item in getattr(output, "content", []) or []:
                text_value = getattr(item, "text", None)
                if text_value:
                    texts.append(text_value)
        return "".join(texts)

    def _create_response(
            self,
            messages: List[Dict[str, Any]],
            is_stream: bool,
            track_history: bool = False) -> Union[str, Iterator[str]]:
        kwargs = self._build_response_kwargs(messages)
        if is_stream:
            return self._stream_response(kwargs, track_history)

        response = self.client.responses.create(**kwargs)
        self._update_stats(getattr(response, "usage", None))
        response_text = self._extract_response_text(response)
        if track_history:
            self.history.append({"role": "assistant", "content": response_text})
        return response_text

    def _stream_response(
            self,
            kwargs: Dict[str, Any],
            track_history: bool = False) -> Iterator[str]:
        def generator() -> Iterator[str]:
            chunks: List[str] = []
            with self.client.responses.stream(**kwargs) as stream:
                for event in stream:
                    event_type = getattr(event, "type", "")
                    delta = getattr(event, "delta", None)
                    if event_type == "response.output_text.delta" and isinstance(delta, str) and delta:
                        chunks.append(delta)
                        yield delta
                final_response = stream.get_final_response()

            self._update_stats(getattr(final_response, "usage", None))
            final_text = self._extract_response_text(final_response) or "".join(chunks)
            if track_history:
                self.history.append({"role": "assistant", "content": final_text})

        return generator()

    def _encode_image_to_base64(self, image_path: str) -> str:
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            return f"data:image/jpeg;base64,{base64_image}"

    def _unified_tool_stream(self, messages: List[Dict[str, str]],
                             tools: List[Dict[str, Any]],
                             function_module: Any) -> Iterator[str]:
        try:
            response_stream = self._create_chat_completion(messages,
                                                           True,
                                                           tools,
                                                           raw_response=True)
            full_response = ""
            tool_calls = []

            for chunk in response_stream:
                if isinstance(chunk, str):
                    content = chunk
                elif hasattr(chunk, 'choices') and chunk.choices:
                    delta = chunk.choices[0].delta
                    content = delta.content if hasattr(
                        delta,
                        'content') and delta.content is not None else None
                    if hasattr(delta, 'tool_calls') and delta.tool_calls:
                        for tool_call in delta.tool_calls:
                            if tool_call.index >= len(tool_calls):
                                tool_calls.append({
                                    "id": tool_call.id,
                                    "type": "function",
                                    "function": {
                                        "name":
                                        tool_call.function.name,
                                        "arguments":
                                        tool_call.function.arguments or ""
                                    }
                                })
                            else:
                                tool_calls[tool_call.index]["function"][
                                    "arguments"] += tool_call.function.arguments or ""
                if content:
                    yield content
                    full_response += content

            if tool_calls:
                tool_outputs = self._execute_tool_calls(
                    tool_calls, function_module)
                tool_results = []
                for tool_output in tool_outputs:
                    result = f"Tool {tool_output['tool_call_id']} returned result: {tool_output['content']}"
                    tool_results.append(result)
                    yield result + "\n"

                tool_result_message = "\n".join(tool_results)
                messages.append({
                    "role":
                    "assistant",
                    "content":
                    f"{full_response}\n\nTool call results:\n{tool_result_message}"
                })

                explanation_request = "Please explain the above tool call results and provide a concise answer."
                messages.append({
                    "role": "user",
                    "content": explanation_request
                })

                explanation_stream = self._create_chat_completion(
                    messages, True, tools, raw_response=True)
                for chunk in explanation_stream:
                    if isinstance(chunk, str):
                        yield chunk
                    elif hasattr(chunk, 'choices') and chunk.choices:
                        delta = chunk.choices[0].delta
                        content = delta.content if hasattr(
                            delta,
                            'content') and delta.content is not None else None
                        if content:
                            yield content
            elif full_response.strip():
                yield f"\n{full_response}\n"
            else:
                yield "\nUnable to generate a response. Please try again.\n"
        except Exception as e:
            yield f"An error occurred: {str(e)}"

        self.history = [
            msg for msg in messages[-5:] if msg.get('content', '').strip()
        ]

    def _create_chat_completion(
            self,
            messages: List[Dict[str, str]],
            is_stream: bool,
            tools: List[Dict[str, Any]] = None,
            raw_response: bool = False) -> Union[str, Iterator[str], Any]:
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "presence_penalty": self.presence_penalty,
            "frequency_penalty": self.frequency_penalty,
            "stop": self.stop,
            "stream": is_stream
        }
        if self.max_output_tokens is not None:
            kwargs["max_tokens"] = self.max_output_tokens
        if tools:
            kwargs["tools"] = tools

        completion = self.client.chat.completions.create(**kwargs)
        if is_stream:
            return completion if raw_response else self._process_stream(
                completion)
        else:
            response = completion.choices[0].message.content
            self._update_stats(completion.usage)
            return response

    def _process_tool_response(self, response, tools: List[Dict[str, Any]],
                               function_module: Any) -> str:
        assistant_output = response.choices[0].message

        if hasattr(assistant_output,
                   'tool_calls') and assistant_output.tool_calls:
            self.history.append({
                "role": "assistant",
                "content": assistant_output.content,
                "tool_calls": assistant_output.tool_calls
            })
            tool_outputs = self._execute_tool_calls(
                assistant_output.tool_calls, function_module)
            self.history.extend(tool_outputs)
            second_response = self._create_chat_completion(
                self.history, False, tools, raw_response=True)
            final_output = second_response.choices[0].message.content or ""
            self.history.append({
                "role": "assistant",
                "content": final_output
            })
        else:
            self.history.append({
                "role": "assistant",
                "content": assistant_output.content
            })
            final_output = assistant_output.content or ""

        return final_output

    def tool_invoke(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "presence_penalty": self.presence_penalty,
            "frequency_penalty": self.frequency_penalty,
            "stop": self.stop,
            "tools": tools,
            "stream": False
        }
        if self.max_output_tokens is not None:
            kwargs["max_tokens"] = self.max_output_tokens
        completion = self.client.chat.completions.create(**kwargs)
        self._update_stats(completion.usage)
        message = completion.choices[0].message
        return self._normalize_tool_invoke_response(
            getattr(message, "content", "") or "",
            getattr(message, "tool_calls", None)
        )

    def _process_stream(self, stream) -> Iterator[str]:
        full_response = ""
        for chunk in stream:
            if hasattr(chunk, 'choices') and chunk.choices:
                delta = chunk.choices[0].delta
                if hasattr(delta, 'content') and delta.content:
                    full_response += delta.content
                    yield delta.content
        self.history.append({"role": "assistant", "content": full_response})

    def _execute_tool_calls(self, tool_calls,
                            function_module: Any) -> List[Dict[str, str]]:
        tool_outputs = []
        for tool_call in tool_calls:
            if isinstance(tool_call, dict):
                function_info = tool_call.get("function", {}) or {}
                tool_name = function_info.get("name", "")
                raw_arguments = function_info.get("arguments", "")
                tool_call_id = tool_call.get("id", "")
            else:
                tool_name = tool_call.function.name
                raw_arguments = tool_call.function.arguments
                tool_call_id = tool_call.id
            try:
                tool_args = json.loads(raw_arguments)
            except json.JSONDecodeError:
                tool_args = {}

            if hasattr(function_module, tool_name):
                tool_func = getattr(function_module, tool_name)
                try:
                    tool_output = tool_func(**tool_args)
                    tool_outputs.append({
                        "name": tool_name,
                        "content": str(tool_output),
                        "tool_call_id": tool_call_id
                    })
                except Exception as e:
                    tool_outputs.append({
                        "name": tool_name,
                        "content": f"Error executing {tool_name}: {str(e)}",
                        "tool_call_id": tool_call_id
                    })
            else:
                tool_outputs.append({
                    "name": tool_name,
                    "content": f"Error: Function {tool_name} not found.",
                    "tool_call_id": tool_call_id
                })

        return tool_outputs

    def _update_stats(self, usage: Any):
        self.chat_count += 1
        if usage is None:
            return
        total_tokens = getattr(usage, "total_tokens", None)
        if total_tokens is None and isinstance(usage, dict):
            total_tokens = usage.get("total_tokens")
        if total_tokens is None:
            input_tokens = getattr(usage, "input_tokens", 0)
            output_tokens = getattr(usage, "output_tokens", 0)
            if isinstance(usage, dict):
                input_tokens = usage.get("input_tokens", input_tokens)
                output_tokens = usage.get("output_tokens", output_tokens)
            total_tokens = (input_tokens or 0) + (output_tokens or 0)
        self.token_count += total_tokens or 0

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_chats": self.chat_count,
            "total_tokens": self.token_count
        }

    def clear_chat(self) -> None:
        self.history = []

    def audio_chat(self, message: str, audio_path: str) -> str:
        raise NotImplementedError("OpenAI API does not support audio chat.")

    def video_chat(self, message: str, video_path: str) -> str:
        raise NotImplementedError("OpenAI API does not support video chat.")
