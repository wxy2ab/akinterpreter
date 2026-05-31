import copy
from typing import Iterator, List, Dict, Any, Literal, Optional, Union
from openai import OpenAI
import json
from ._llm_api_client import LLMApiClient
from ..utils.config_setting import Config
from ..utils.handle_max_tokens import handle_max_tokens
from tenacity import retry, stop_after_attempt, wait_exponential
import logging
import httpx

logger = logging.getLogger(__name__)

class SimpleDeepSeekClient(LLMApiClient):
    supports_structured_output = True

    def __init__(self, api_key: str = "", base_url: str = "https://api.deepseek.com/",model:str = "deepseek-v4-flash",
                 max_tokens: int = 64000, temperature: float = 1.0, top_p: float = 1,
                 presence_penalty: float = 0, frequency_penalty: float = 0, stop: Union[str, List[str]] = None,
                 reasoning_effort: Optional[str] = "high", extra_body: Optional[Dict[str, Any]] = None,
                 thinking: bool = True):
        config = Config()
        if api_key == "" :
            api_key = config.get("deep_seek_api_key")
            
        # 自定义httpx客户端以处理DeepSeek API偶尔的连接中断问题
        http_client = httpx.Client(
            limits=httpx.Limits(max_keepalive_connections=100, max_connections=200),
            timeout=httpx.Timeout(timeout=600.0, connect=60.0, read=600.0, write=120.0)
        )
        
        self.client = OpenAI(
            api_key=api_key, 
            base_url=base_url,
            http_client=http_client,
            max_retries=5  # OpenAI客户端内置重试
        )
        self.task = "代码"
        self.chat_count = 0
        self.token_count = 0
        self.prompt_token_count = 0
        self.completion_token_count = 0
        self.history = []
        self._model_list = [
            "deepseek-v4-flash",
            "deepseek-v4-pro",
            "deepseek-chat",
            "deepseek-coder",
            "deepseek-reasoner",
        ]
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.presence_penalty = presence_penalty
        self.frequency_penalty = frequency_penalty
        self.stop = stop
        self.reasoning_effort = reasoning_effort
        self.extra_body = copy.deepcopy(extra_body) if extra_body is not None else {
            "thinking": {
                "type": "enabled" if thinking else "disabled"
            }
        }
        self.thinking = thinking
        self._last_reasoning_content = None
        self._response_format: Optional[Dict[str, Any]] = None
        if model=="deepseek-chat":
            self.max_tokens = 8192
        elif "speciale" in model:
            self.max_tokens = 128000

    def set_system_message(self, system_message: str = "你是一个智能助手,擅长把复杂问题清晰明白通俗易懂地解答出来"):
        self.history = [{"role": "system", "content": system_message}]

    def set_response_format(self, fmt: Optional[Dict[str, Any]]) -> None:
        if fmt is not None and not isinstance(fmt, dict):
            raise TypeError("response_format must be a dict or None")
        self._response_format = fmt

    def set_task(self, task: str, model: Optional[str] = None) -> None:
        """
        设置任务类型和对应的temperature参数
        
        根据 DeepSeek 官方文档建议：
        - 代码生成/数学解题: 0.0
        - 数据抽取/分析: 1.0
        - 通用对话: 1.3
        - 翻译: 1.3
        - 创意类写作: 1.5
        - 工具调用: 0.0 (需要准确的决策)
        """
        if task == "代码":
            self.model = "deepseek-coder"
            self.temperature = 0.0  # 代码生成需要高准确性
        elif task == "数据分析":
            self.model = "deepseek-chat"
            self.temperature = 1.0  # 按官方文档建议
        elif task == "对话":
            self.model = "deepseek-chat"
            self.temperature = 1.3  # 按官方文档建议
        elif task == "翻译":
            self.model = "deepseek-chat"
            self.temperature = 1.3  # 按官方文档建议
        elif task == "创意":
            self.model = "deepseek-chat"
            self.temperature = 1.5  # 按官方文档建议
        elif task == "工具调用":
            # 工具调用需要准确的决策，类似代码生成
            self.model = "deepseek-chat"
            self.temperature = 0.0
        else:
            raise ValueError("不支持的任务类型")

        if model is not None:
            self.model = model
        self.task = task
        self.messages = []
    
    def set_report(self):
        self.set_task(task = "数据分析" )

    @staticmethod
    def _sanitize_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove orphan tool messages that lack a preceding assistant with
        matching tool_calls.  DeepSeek strictly requires every ``role=tool``
        message to have a matching ``tool_call_id`` in the immediately
        preceding ``role=assistant`` message.

        Also handles CCD internal message format (``kind=assistant_tool_use``)
        by synthesising a ``tool_calls`` array so downstream ``role=tool``
        messages are not incorrectly dropped.
        """
        result: List[Dict[str, Any]] = []
        last_assistant_tool_call_ids: set[str] = set()
        for msg in messages:
            role = msg.get("role")
            if role == "assistant":
                tcs = msg.get("tool_calls") or []
                # CCD internal format: assistant_tool_use carries tool_use_id
                # but no OpenAI-style tool_calls.  Synthesize one so paired
                # tool-result messages survive the orphan check.
                if not tcs and msg.get("kind") == "assistant_tool_use":
                    tcid = msg.get("tool_use_id")
                    if not tcid:
                        meta = msg.get("metadata") or {}
                        tcid = meta.get("tool_use_id")
                    if tcid:
                        tool_name = msg.get("tool_name") or ""
                        if not tool_name:
                            content = str(msg.get("content", ""))
                            if content.startswith("tool:"):
                                tool_name = content[5:]
                        tcs = [{
                            "id": str(tcid),
                            "type": "function",
                            "function": {
                                "name": tool_name or "unknown",
                                "arguments": "{}",
                            },
                        }]
                        msg = dict(msg)
                        msg["tool_calls"] = tcs
                last_assistant_tool_call_ids = {
                    str(t.get("id")) for t in tcs if isinstance(t, dict) and t.get("id")
                }
                result.append(msg)
            elif role == "tool":
                tcid = str(msg.get("tool_call_id", ""))
                if tcid in last_assistant_tool_call_ids:
                    result.append(msg)
                else:
                    # Orphan tool message — drop it to avoid DeepSeek 400
                    continue
            else:
                result.append(msg)
        return result

    def _build_request_kwargs(
        self,
        messages: List[Dict[str, Any]],
        is_stream: bool,
        tools: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        # DeepSeek thinking mode requires reasoning_content to be passed back
        # in multi-turn conversations.  Every assistant message in the
        # history that was produced in thinking mode must carry the field.
        # We inject the cached value into *all* assistant messages that
        # lack it, not only the last one, because DeepSeek validates the
        # entire message sequence.
        messages = [dict(m) for m in messages]
        if self._last_reasoning_content:
            for msg in messages:
                if msg.get("role") == "assistant" and "reasoning_content" not in msg:
                    msg["reasoning_content"] = self._last_reasoning_content
        # Sanitize orphan tool messages before sending to DeepSeek
        messages = self._sanitize_messages(messages)
        kwargs = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "presence_penalty": self.presence_penalty,
            "frequency_penalty": self.frequency_penalty,
            "stop": self.stop,
            "stream": is_stream
        }

        if self.reasoning_effort is not None:
            kwargs["reasoning_effort"] = self.reasoning_effort

        extra_body = copy.deepcopy(self.extra_body)
        if "thinking" not in extra_body:
            extra_body["thinking"] = {
                "type": "enabled" if self.thinking else "disabled"
            }
        if extra_body:
            kwargs["extra_body"] = extra_body

        if self._response_format:
            kwargs["response_format"] = self._response_format

        if tools:
            kwargs["tools"] = tools

        return kwargs

        
    @handle_max_tokens
    def text_chat(self, message: str, is_stream: bool = False) -> Union[str, Iterator[str]]:
        if not self.history:
            self.set_system_message()
        
        # 主动检查并压缩上下文（预防性措施）
        self._check_and_compress_history()
        
        self.history.append({"role": "user", "content": message})
        try:
            return self._create_chat_completion(self.history, is_stream)
        except Exception as e:
            # 检查是否是上下文长度超限错误
            error_msg = str(e)
            if "maximum context length" in error_msg or "context_length_exceeded" in error_msg:
                logger.warning(f"⚠️ text_chat上下文长度超限，开始压缩历史消息")
                self._compress_history()
                logger.info(f"✅ 压缩后历史消息数量: {len(self.history)}")
                return self._create_chat_completion(self.history, is_stream)
            else:
                raise

    @retry(stop=stop_after_attempt(10), wait=wait_exponential(multiplier=2, min=5, max=60))
    def one_chat(self, message: str, is_stream: bool = False) -> Union[str, Iterator[str]]:
        if not self.history:
            self.set_system_message()
        msg = [{"role": "user", "content": message}] if isinstance(message, str) else message
        return self._create_chat_completion(msg, is_stream)

    def tool_chat(self, user_message: str, tools: List[Dict[str, Any]], function_module: Any, is_stream: bool = False) -> Union[str, Iterator[str]]:
        if not self.history:
            self.set_system_message()
        
        # 主动检查并压缩上下文（预防性措施）
        self._check_and_compress_history()
        
        self.history.append({"role": "user", "content": user_message})
        if is_stream:
            return self._unified_tool_stream(self.history, tools, function_module)
        else:
            # 直接获取完整response对象，保留tool_calls供后续处理
            kwargs = self._build_request_kwargs(self.history, False, tools)

            try:
                completion = self.client.chat.completions.create(**kwargs)
                return self._process_tool_response(completion, tools, function_module)
            except Exception as e:
                # 检查是否是上下文长度超限错误或工具调用协议错误
                error_msg = str(e)
                if "maximum context length" in error_msg or "context_length_exceeded" in error_msg:
                    logger.warning(f"⚠️ 上下文长度超限，开始压缩历史消息")
                    # 压缩历史消息并重试
                    self._compress_history()
                    kwargs["messages"] = self.history
                    logger.info(f"✅ 压缩后历史消息数量: {len(self.history)}")
                    completion = self.client.chat.completions.create(**kwargs)
                    return self._process_tool_response(completion, tools, function_module)
                elif "must be a response to a preceding message with 'tool_calls'" in error_msg:
                    logger.warning(f"⚠️ 工具调用协议错误，压缩历史消息后重试")
                    # 压缩历史消息并重试
                    self._compress_history()
                    kwargs["messages"] = self.history
                    logger.info(f"✅ 压缩后历史消息数量: {len(self.history)}")
                    completion = self.client.chat.completions.create(**kwargs)
                    return self._process_tool_response(completion, tools, function_module)
                else:
                    # 其他错误直接抛出
                    raise

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
        kwargs = self._build_request_kwargs(messages, is_stream, tools)
        completion = self.client.chat.completions.create(**kwargs)
        if is_stream:
            return completion if raw_response else self._process_stream(completion)
        else:
            if raw_response:
                return completion
            message = completion.choices[0].message
            self._last_reasoning_content = getattr(message, "reasoning_content", None)
            response = message.content
            self._update_stats(completion.usage)
            return response

    def tool_invoke(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        kwargs = self._build_request_kwargs(messages, False, tools)
        completion = self.client.chat.completions.create(**kwargs)
        self._update_stats(completion.usage)
        message = completion.choices[0].message
        return self._normalize_tool_invoke_response(
            getattr(message, "content", "") or "",
            getattr(message, "tool_calls", None),
            reasoning_content=getattr(message, "reasoning_content", None),
        )

    def _process_tool_response(self, response, tools: List[Dict[str, Any]], function_module: Any) -> str:
        """处理工具调用的响应"""
        try:
            # 如果响应已经是字符串，直接返回
            if isinstance(response, str):
                logger.debug("⚠️ 响应已经是字符串格式，直接返回")
                return response
            
            # 如果响应是OpenAI格式的对象
            if hasattr(response, 'choices') and response.choices:
                assistant_output = response.choices[0].message
                self._update_stats(response.usage)

                # 添加调试日志
                logger.info(f"🔍 检查tool_calls: has_tool_calls={hasattr(assistant_output, 'tool_calls')}")
                if hasattr(assistant_output, 'tool_calls'):
                    logger.info(f"🔍 tool_calls值: {assistant_output.tool_calls}")
                logger.info(f"🔍 message content: {assistant_output.content[:200] if assistant_output.content else 'None'}...")

                if hasattr(assistant_output, 'tool_calls') and assistant_output.tool_calls:
                    logger.info(f"✅ 检测到 {len(assistant_output.tool_calls)} 个工具调用")
                    for i, call in enumerate(assistant_output.tool_calls):
                        logger.info(f"   {i+1}. {call.function.name}")
                    
                    self.history.append({"role": "assistant", "content": assistant_output.content, "tool_calls": assistant_output.tool_calls})
                    tool_outputs = self._execute_tool_calls(assistant_output.tool_calls, function_module)
                    self.history.extend(tool_outputs)
                    
                    # 第二次调用API获取最终响应
                    kwargs = self._build_request_kwargs(self.history, False, tools)
                    
                    try:
                        second_completion = self.client.chat.completions.create(**kwargs)
                        self._update_stats(second_completion.usage)
                        final_output = second_completion.choices[0].message.content
                    except Exception as e:
                        # 检查是否是上下文长度超限错误或工具调用协议错误
                        error_msg = str(e)
                        if "maximum context length" in error_msg or "context_length_exceeded" in error_msg:
                            logger.warning(f"⚠️ 第二次调用时上下文长度超限，压缩历史后重试")
                            self._compress_history()
                            kwargs["messages"] = self.history
                            logger.info(f"✅ 压缩后历史消息数量: {len(self.history)}")
                            second_completion = self.client.chat.completions.create(**kwargs)
                            self._update_stats(second_completion.usage)
                            final_output = second_completion.choices[0].message.content
                        elif "must be a response to a preceding message with 'tool_calls'" in error_msg:
                            logger.warning(f"⚠️ 第二次调用时工具调用协议错误，压缩历史后重试")
                            self._compress_history()
                            kwargs["messages"] = self.history
                            logger.info(f"✅ 压缩后历史消息数量: {len(self.history)}")
                            second_completion = self.client.chat.completions.create(**kwargs)
                            self._update_stats(second_completion.usage)
                            final_output = second_completion.choices[0].message.content
                        else:
                            raise
                else:
                    self.history.append({"role": "assistant", "content": assistant_output.content})
                    final_output = assistant_output.content
                
                return final_output
            
            # 如果响应是其他格式，尝试转换为字符串
            else:
                logger.warning(f"未知响应格式: {type(response)}")
                return str(response)
                
        except Exception as e:
            logger.error(f"处理工具响应失败: {e}")
            # 如果处理失败，尝试将response转换为字符串
            return str(response)

    def _process_stream(self, stream) -> Iterator[str]:
        full_response = ""
        for chunk in stream:
            if hasattr(chunk, 'choices') and chunk.choices:
                delta = chunk.choices[0].delta
                if hasattr(delta, 'content') and delta.content:
                    full_response += delta.content
                    yield delta.content
        self.history.append({"role": "assistant", "content": full_response})

    def _execute_tool_calls(self, tool_calls, function_module: Any) -> List[Dict[str, str]]:
        tool_outputs = []
        for tool_call in tool_calls:
            # 处理两种可能的格式：字典和对象
            if isinstance(tool_call, dict):
                tool_name = tool_call['function']['name']
                tool_id = tool_call['id']
                tool_args_str = tool_call['function']['arguments']
            else:
                tool_name = tool_call.function.name
                tool_id = tool_call.id
                tool_args_str = tool_call.function.arguments
            
            logger.info(f"🔧 执行工具: {tool_name}")
            
            try:
                tool_args = json.loads(tool_args_str)
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ 解析工具参数失败: {e}")
                tool_args = {}
            
            if hasattr(function_module, tool_name):
                tool_func = getattr(function_module, tool_name)
                try:
                    logger.info(f"   参数: {tool_args}")
                    tool_output = tool_func(**tool_args)
                    logger.info(f"   结果: {str(tool_output)[:200]}...")
                    tool_outputs.append({
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "name": tool_name,
                        "content": str(tool_output)
                    })
                except Exception as e:
                    logger.error(f"❌ 执行工具失败 {tool_name}: {e}")
                    import traceback
                    traceback.print_exc()
                    tool_outputs.append({
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "name": tool_name,
                        "content": f"Error executing {tool_name}: {str(e)}"
                    })
            else:
                logger.error(f"❌ 工具函数未找到: {tool_name}")
                tool_outputs.append({
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "name": tool_name,
                    "content": f"Error: Function {tool_name} not found."
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
                normalized_usage["prompt_tokens"] + normalized_usage["completion_tokens"]
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

    def _check_and_compress_history(self, token_threshold: int = 1000000) -> None:
        """
        检查历史消息总长度，如果超过阈值则主动压缩
        
        Args:
            token_threshold: 触发压缩的token数阈值（默认1M tokens）
        """
        if not self.history:
            return
        
        # 计算非系统消息的总长度
        non_system_messages = [msg for msg in self.history if msg.get('role') != 'system']
        
        # 计算总字符数（粗略估算token数）
        total_chars = sum(len(str(msg.get('content', ''))) for msg in non_system_messages)
        total_chars += sum(len(str(msg.get('tool_calls', ''))) for msg in non_system_messages if msg.get('tool_calls'))
        
        estimated_tokens = total_chars
        
        if estimated_tokens > token_threshold:
            logger.info(f"📊 历史消息总长度(约{estimated_tokens:,}tokens, {len(non_system_messages)}条)超过阈值({token_threshold:,}tokens)，主动压缩")
            self._compress_history()
        else:
            logger.debug(f"📊 历史消息总长度(约{estimated_tokens:,}tokens, {len(non_system_messages)}条)在安全范围内")
    
    def _compress_history(self, keep_recent_rounds: int = 3) -> None:
        """
        压缩历史消息，保留系统消息和最近N轮对话
        
        Args:
            keep_recent_rounds: 保留最近的轮次数（默认3轮，更激进的压缩）
        """
        if not self.history:
            return
        
        # 分离系统消息和其他消息
        system_messages = [msg for msg in self.history if msg.get('role') == 'system']
        other_messages = [msg for msg in self.history if msg.get('role') != 'system']
        
        # 🔧 修复：基于消息总长度而不是数量来判断是否需要压缩
        # 计算消息总字符数（粗略估算token数：中文约1字符=1token，英文约4字符=1token）
        total_chars = sum(len(str(msg.get('content', ''))) for msg in other_messages)
        total_chars += sum(len(str(msg.get('tool_calls', ''))) for msg in other_messages if msg.get('tool_calls'))
        
        # 估算总token数（保守估计：每个字符约1token）
        estimated_tokens = total_chars
        
        # DeepSeek的上下文限制通常是64K tokens，我们保守设置为50K
        # 如果总长度小于20K tokens，且消息数量少于20条，则无需压缩
        if estimated_tokens < 20000 and len(other_messages) <= 20:
            logger.info(f"消息总长度较小(约{estimated_tokens:,}tokens, {len(other_messages)}条消息)，无需压缩")
            return
        
        logger.info(f"消息总长度较大(约{estimated_tokens:,}tokens, {len(other_messages)}条消息)，需要压缩")
        
        logger.info(f"开始压缩历史消息: 原始数量={len(self.history)}, 保留最近{keep_recent_rounds}轮")
        
        # 计算要保留的消息
        # 每轮对话通常包含: user -> assistant (可能有tool_calls) -> tool -> assistant
        # 我们保留最近的消息
        messages_to_keep = keep_recent_rounds * 4  # 估算每轮最多4条消息
        recent_messages = other_messages[-messages_to_keep:]
        
        # 🔧 修复工具调用协议问题：确保tool消息前有对应的assistant消息
        # 如果第一条保留的消息是tool消息，需要向前找到对应的assistant消息
        if recent_messages and recent_messages[0].get('role') == 'tool':
            logger.warning("⚠️ 检测到保留的第一条消息是tool消息，需要向前查找对应的assistant消息")
            # 从截断点向前查找，找到最近的带tool_calls的assistant消息
            start_idx = len(other_messages) - messages_to_keep - 1
            while start_idx >= 0:
                msg = other_messages[start_idx]
                if msg.get('role') == 'assistant' and msg.get('tool_calls'):
                    # 找到了，将这条消息也包含进来
                    logger.info(f"✅ 找到对应的assistant消息，向前扩展保留范围")
                    recent_messages = other_messages[start_idx:]
                    break
                start_idx -= 1
            
            # 如果没找到对应的assistant消息，移除开头的tool消息
            if start_idx < 0:
                logger.warning("⚠️ 未找到对应的assistant消息，移除孤立的tool消息")
                # 移除所有开头的tool消息，直到遇到非tool消息
                while recent_messages and recent_messages[0].get('role') == 'tool':
                    recent_messages.pop(0)
        
        # 创建历史摘要
        old_messages_count = len(other_messages) - len(recent_messages)
        if old_messages_count > 0:
            old_messages = other_messages[:old_messages_count]
            summary = self._create_history_summary(old_messages)
            logger.info(f"创建历史摘要: {len(old_messages)} 条消息 -> 1 条摘要")
            
            # 重建历史: 系统消息 + 摘要 + 最近消息
            self.history = system_messages + [summary] + recent_messages
        else:
            # 重建历史: 系统消息 + 最近消息
            self.history = system_messages + recent_messages
        
        # 🔧 验证压缩后的长度
        compressed_chars = sum(len(str(msg.get('content', ''))) for msg in self.history)
        compressed_chars += sum(len(str(msg.get('tool_calls', ''))) for msg in self.history if msg.get('tool_calls'))
        compressed_tokens = compressed_chars
        
        logger.info(f"压缩完成: {len(self.history)} 条消息, 约{compressed_tokens:,}tokens")
        
        # 🔧 更激进的递归压缩策略：如果压缩后还是太长（超过100K tokens），继续压缩
        # 降低阈值从500K到100K，更早触发二次压缩
        if compressed_tokens > 100000 and keep_recent_rounds > 1:
            logger.warning(f"⚠️ 压缩后仍然过长({compressed_tokens:,}tokens)，进行更激进的压缩")
            # 更激进：直接减半，最少保留1轮
            self._compress_history(keep_recent_rounds=max(1, keep_recent_rounds // 2))
    
    def _create_history_summary(self, messages: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        创建历史消息的摘要（更激进、更简洁）
        
        Args:
            messages: 要摘要的消息列表
            
        Returns:
            摘要消息（user角色）
        """
        # 统计关键信息
        user_messages = [m for m in messages if m.get('role') == 'user']
        assistant_messages = [m for m in messages if m.get('role') == 'assistant']
        tool_messages = [m for m in messages if m.get('role') == 'tool']
        
        # 提取工具调用信息（去重）
        tool_calls_set = set()
        for msg in assistant_messages:
            if msg.get('tool_calls'):
                for call in msg.get('tool_calls', []):
                    if isinstance(call, dict):
                        func_name = call.get('function', {}).get('name', 'unknown')
                    else:
                        func_name = getattr(call.function, 'name', 'unknown') if hasattr(call, 'function') else 'unknown'
                    tool_calls_set.add(func_name)
        
        # 🔧 更激进的压缩：只保留最关键的统计信息
        # 创建超级简洁的摘要文本（一行描述）
        summary_text = f"[已压缩历史] {len(messages)}条消息已被压缩为此摘要，包含{len(user_messages)}轮对话、{len(tool_messages)}次工具调用。继续优化任务，关注最近的结果。"
        
        return {
            "role": "user",
            "content": summary_text.strip()
        }

    def image_chat(self, message: str, image_path: str) -> str:
        raise NotImplementedError("MoonShot API does not support image chat.")

    def audio_chat(self, message: str, audio_path: str) -> str:
        raise NotImplementedError("MoonShot API does not support audio chat.")

    def video_chat(self, message: str, video_path: str) -> str:
        raise NotImplementedError("MoonShot API does not support video chat.")
