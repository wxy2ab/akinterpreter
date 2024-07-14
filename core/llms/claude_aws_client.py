import asyncio
import logging
from typing import Generator, Iterator, List, Dict, Any, Optional, Union
from anthropic import AnthropicBedrock
from anthropic.types import MessageStreamEvent, ContentBlockDeltaEvent
import boto3
import json
import os
import base64
from PIL import Image
import io
from ..utils.retry import retry
from ._llm_api_client import LLMApiClient


class ClaudeAwsClient(LLMApiClient):

    def __init__(self,
                 aws_access_key_id: Optional[str] = None,
                 aws_secret_access_key: Optional[str] = None,
                 aws_session_token: Optional[str] = None,
                 aws_region: str = "us-east-1",
                 model: str = "anthropic.claude-3-5-sonnet-20240620-v1:0",
                temperature: float = 0.5,
                top_p: float = 1.0,
                top_k: int = 250,
                max_tokens: int = 5120,
                stop_sequences: Optional[List[str]] = None,
                 ):
        self.aws_region = aws_region
        self.model = model
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.aws_session_token = aws_session_token
        self.client = self._create_client()
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.max_tokens = max_tokens
        self.stop_sequences = stop_sequences or []
        self.history: List[dict] = []
        self.stat: Dict[str, Any] = {
            "call_count": {
                "text_chat": 0,
                "image_chat": 0,
                "tool_chat": 0,
                "pdf_chat": 0
            },
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost": 0  # 如果可能的话，您可能想要根据实际定价计算成本
        }
        self.supported_sizes = [(1092, 1092), (951, 1268), (896, 1344),
                                (819, 1456), (784, 1568)]

    def _get_aws_credentials(self):
        from ..utils.config_setting import Config
        config = Config()
        if config.has_key("aws_access_key_id") and config.has_key(
                "aws_secret_access_key"):
            return {
                "aws_access_key": config.get("aws_access_key_id"),
                "aws_secret_key": config.get("aws_secret_access_key"),
                "aws_session_token": None
            }
        if self.aws_access_key_id and self.aws_secret_access_key:
            return {
                "aws_access_key": self.aws_access_key_id,
                "aws_secret_key": self.aws_secret_access_key,
                "aws_session_token": self.aws_session_token
            }

        access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        session_token = os.environ.get('AWS_SESSION_TOKEN')

        if access_key and secret_key:
            return {
                "aws_access_key": access_key,
                "aws_secret_key": secret_key,
                "aws_session_token": session_token
            }

        session = boto3.Session()
        credentials = session.get_credentials()
        if credentials:
            return {
                "aws_access_key": credentials.access_key,
                "aws_secret_key": credentials.secret_key,
                "aws_session_token": credentials.token
            }

        raise ValueError(
            "AWS credentials not found. Please provide credentials or configure your environment."
        )

    def _create_client(self):
        credentials = self._get_aws_credentials()
        return AnthropicBedrock(
            aws_access_key=credentials["aws_access_key"],
            aws_secret_key=credentials["aws_secret_key"],
            aws_session_token=credentials["aws_session_token"],
            aws_region=self.aws_region)

    def _stream_response(self, message: str,
                         max_tokens: Optional[int]=None) -> Generator[str, None, None]:
        response = self.client.messages.create(model=self.model,
                                            max_tokens=max_tokens,
                                            messages=self.history,
                                            model=self.model,
                                            max_tokens=max_tokens or self.max_tokens,
                                            temperature=self.temperature,
                                            top_p=self.top_p,
                                            top_k=self.top_k,
                                            stop_sequences=self.stop_sequences,
                                            stream=True)
        full_response = ""
        for event in response:
            if isinstance(event, ContentBlockDeltaEvent) and event.delta.text:
                content = event.delta.text
                full_response += content
                yield content

        self.history.append({"role": "assistant", "content": full_response})
        self.stat["call_count"]["text_chat"] += 1

    def _update_usage_stats(self, response):
        if hasattr(response, 'usage'):
            usage = response.usage
            self.stat["total_input_tokens"] += usage.input_tokens
            self.stat["total_output_tokens"] += usage.output_tokens

    def text_chat(self,
                  message: str,
                  max_tokens: Optional[ int] = None,
                  is_stream: bool = False) -> Union[str, Iterator[str]]:
        self.history.append({"role": "user", "content": message})

        if is_stream:
            return self._stream_response(message, max_tokens)
        else:
            response = self.client.messages.create(model=self.model,
                                                   max_tokens=max_tokens,
                                                   messages=self.history,
                                                max_tokens=max_tokens or self.max_tokens,
                                                temperature=self.temperature,
                                                top_p=self.top_p,
                                                top_k=self.top_k,
                                                stop_sequences=self.stop_sequences,
                                                   )
            assistant_message = response.content[0].text
            self.history.append({
                "role": "assistant",
                "content": assistant_message
            })
            self.stat["call_count"]["text_chat"] += 1
            self._update_usage_stats(response)
            return assistant_message

    def one_chat(self,
                 message: Union[str, List[Union[str, Any]]],
                 max_tokens: Optional[ int] = None,
                 is_stream: bool = False) -> Union[str, Iterator[str]]:
        msg = None
        if isinstance(message, list):
            msg = message
        else:
            msg = [{"role": "user", "content": message}]

        if is_stream:
            return self._stream_one_response(msg, max_tokens)
        else:

            @retry(3)
            def send_message():
                response = self.client.messages.create(model=self.model,
                                                       max_tokens=max_tokens,
                                                       messages=msg,
                                            max_tokens=max_tokens or self.max_tokens,
                                            temperature=self.temperature,
                                            top_p=self.top_p,
                                            top_k=self.top_k,
                                            stop_sequences=self.stop_sequences
                                                       )
                return response

            response = send_message()
            assistant_message = response.content[0].text
            self.stat["call_count"]["text_chat"] += 1
            self._update_usage_stats(response)
            return assistant_message

    def _stream_one_response(self, msg: List[Dict[str, str]],
                             max_tokens: int) -> Generator[str, None, None]:
        response = self.client.messages.create(model=self.model,
                                               max_tokens=max_tokens,
                                               messages=msg,
                                            max_tokens=max_tokens or self.max_tokens,
                                            temperature=self.temperature,
                                            top_p=self.top_p,
                                            top_k=self.top_k,
                                            stop_sequences=self.stop_sequences,
                                               stream=True)
        for event in response:
            if isinstance(event, ContentBlockDeltaEvent) and event.delta.text:
                yield event.delta.text

        self.stat["call_count"]["text_chat"] += 1

    def image_chat(self,
                   message: str,
                   image_url: str,
                   max_tokens: int = 10240) -> str:
        image_message = {
            "role":
            "user",
            "content": [{
                "type": "image",
                "source": {
                    "type": "url",
                    "url": image_url
                }
            }, {
                "type": "text",
                "text": message
            }]
        }
        self.history.append(image_message)
        response = self.client.messages.create(model=self.model,
                                               max_tokens=max_tokens,
                                               messages=self.history,
                                            max_tokens=max_tokens or self.max_tokens,
                                            temperature=self.temperature,
                                            top_p=self.top_p,
                                            top_k=self.top_k,
                                            stop_sequences=self.stop_sequences,
                                               )
        assistant_message = response.content[0].text
        self.history.append({
            "role": "assistant",
            "content": assistant_message
        })
        self.stat["call_count"]["image_chat"] += 1
        self._update_usage_stats(response)
        return assistant_message

    def image64_chat(self,
                     message: str,
                     image_path: str,
                     max_tokens: int = 10240) -> str:
        # 读取并调整图片大小
        with Image.open(image_path) as img:
            resized_img = self._resize_image(img)
            resized_img.format = img.format  # 保留原始格式

            # 将调整后的图片转换为 base64
            buffered = io.BytesIO()
            resized_img.save(buffered, format=resized_img.format)
            base64_image = base64.b64encode(
                buffered.getvalue()).decode('utf-8')

        # 构建消息
        image_message = {
            "role":
            "user",
            "content": [{
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": self._get_media_type(image_path),
                    "data": base64_image
                }
            }, {
                "type": "text",
                "text": message
            }]
        }
        self.history.append(image_message)

        # 调用 Claude API
        response = self.client.messages.create(model=self.model,
                                               max_tokens=max_tokens,
                                               messages=self.history,
                                            max_tokens=max_tokens or self.max_tokens,
                                            temperature=self.temperature,
                                            top_p=self.top_p,
                                            top_k=self.top_k,
                                            stop_sequences=self.stop_sequences,
                                               )

        assistant_message = response.content[0].text
        self.history.append({
            "role": "assistant",
            "content": assistant_message
        })
        self.stat["call_count"]["image_chat"] += 1
        self._update_usage_stats(response)
        return assistant_message

    def _resize_image(self, img: Image.Image) -> Image.Image:
        original_width, original_height = img.size
        original_aspect_ratio = original_width / original_height

        # 找到最接近原始宽高比的支持尺寸
        closest_size = min(
            self.supported_sizes,
            key=lambda size: abs(size[0] / size[1] - original_aspect_ratio))

        # 调整图片大小
        resized_img = img.resize(closest_size, Image.LANCZOS)
        return resized_img

    def _get_media_type(self, file_path: str) -> str:
        """根据文件扩展名确定媒体类型"""
        extension = os.path.splitext(file_path)[1].lower()
        media_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.webp': 'image/webp'
        }
        return media_types.get(extension, 'application/octet-stream')

    def process_tool_result(self, tool_result):
        if isinstance(tool_result, str):
            try:
                return json.loads(tool_result)
            except json.JSONDecodeError:
                return tool_result
        return tool_result

    def tool_chat(self,
                  user_message: str,
                  tools: List[Dict[str, Any]],
                  function_module: Any,
                  max_tokens: int = 1000,
                  is_stream: bool = False) -> Union[str, Iterator[str]]:
        iterator = ContinuousStreamIterator(self, user_message, tools,
                                            function_module, max_tokens,
                                            is_stream)

        if is_stream:
            return (chunk for chunk in iterator if chunk is not None)
        else:
            return "".join(chunk for chunk in iterator if chunk is not None)

    def one_tool_chat(self,
                      user_message: str,
                      tools: List[Dict[str, Any]],
                      function_module: Any,
                      max_tokens: int = 10000) -> str:
        # 移除工具描述中的 output_schema（如果存在）
        cleaned_tools = []
        for tool in tools:
            cleaned_tool = tool.copy()
            # pop 方法会安全地移除 output_schema，如果它不存在，则返回 None
            cleaned_tool.pop('output_schema', None)
            cleaned_tools.append(cleaned_tool)
        tools = cleaned_tools
        history = []
        history.append({"role": "user", "content": user_message})
        response = self.client.messages.create(model=self.model,
                                               max_tokens=max_tokens,
                                               messages=history,
                                            max_tokens=max_tokens or self.max_tokens,
                                            temperature=self.temperature,
                                            top_p=self.top_p,
                                            top_k=self.top_k,
                                            stop_sequences=self.stop_sequences,
                                               tools=tools)

        assistant_message = ""
        tool_uses = []

        for content in response.content:
            if content.type == 'text':
                assistant_message += content.text
            elif content.type == 'tool_use':
                tool_uses.append(content)

        history.append({"role": "assistant", "content": assistant_message})
        self._update_usage_stats(response)

        function_call_str = ""

        if tool_uses:
            for tool_use in tool_uses:
                function_name = tool_use.name
                function_args = tool_use.input

                if hasattr(function_module, function_name):
                    function = getattr(function_module, function_name)
                    try:
                        tool_result = function(**function_args)
                        tool_result = self.process_tool_result(tool_result)
                    except Exception as e:
                        tool_result = f"Error executing {function_name}: {str(e)}"
                else:
                    tool_result = f"Function {function_name} not found in the provided module."

                history.append({
                    "role":
                    "user",
                    "content":
                    f"工具函数返回结果{function_name}: {tool_result}"
                })
                function_call_str = f"*使用工具*:{function_name}\n*参数:* {function_args} \n*工具结果:*{tool_result}"

            final_response = self.client.messages.create(model=self.model,
                                                         max_tokens=max_tokens,
                                                         messages=history)
            final_assistant_message = "".join([
                content.text for content in final_response.content
                if content.type == 'text'
            ])
            history.append({
                "role": "assistant",
                "content": final_assistant_message
            })
            self.stat["call_count"]["tool_chat"] += 1
            self._update_usage_stats(final_response)
            final_assistant_message = f"*首轮消息：*{assistant_message}\n{function_call_str}\n*最终结果：*{final_assistant_message}"
            return final_assistant_message
        else:
            self.stat["call_count"]["tool_chat"] += 1
            return assistant_message

    def _parse_tool_calls(self, message: str) -> List[Dict[str, Any]]:
        from regex import re
        tool_calls = []
        # 使用正则表达式匹配工具调用
        pattern = r'Function call: (\w+)\((.*?)\)'
        matches = re.findall(pattern, message)
        for match in matches:
            function_name = match[0]
            args_str = match[1]
            try:
                # 尝试解析参数为 JSON
                args = json.loads('{' + args_str + '}')
            except json.JSONDecodeError:
                # 如果解析失败，则将参数作为字符串处理
                args = {'args': args_str}
            tool_calls.append({'name': function_name, 'arguments': args})
        return tool_calls

    def get_history(self) -> List[Dict[str, Any]]:
        return self.history

    def clear_chat(self) -> None:
        self.history.clear()

    def get_stats(self) -> Dict[str, int]:
        return self.stat

    def video_chat(self, message: str, video_path: str) -> str:
        raise NotImplementedError(
            "Video chat is not supported in this version of Claude API client."
        )

    def audio_chat(self, message: str, audio_path: str) -> str:
        raise NotImplementedError(
            "Audio chat is not supported in this version of Claude API client."
        )


logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


class ContinuousStreamIterator:

    def __init__(self, client, initial_message, tools, function_module,
                 max_tokens, is_stream):
        self.client = client
        self.history = [{"role": "user", "content": initial_message}]
        self.tools = tools
        self.function_module = function_module
        self.max_tokens = max_tokens
        self.is_stream = is_stream
        self.current_response = None
        self.tool_uses = []
        self.state = 'initial_response'
        self.buffer = []
        self.assistant_message = ""
        self.initial_response_complete = False

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            if self.buffer:
                return self.buffer.pop(0)

            logger.debug(f"Current state: {self.state}")
            logger.debug(f"Tool uses: {self.tool_uses}")

            if self.state == 'initial_response':
                self._handle_initial_response()
            elif self.state == 'tool_calls':
                self._handle_tool_calls()
            elif self.state == 'final_response':
                self._handle_final_response()
            elif self.state == 'finished':
                raise StopIteration
            else:
                raise StopIteration

    def _handle_initial_response(self):
        if not self.current_response:
            self.current_response = self.client.client.messages.create(
                model=self.client.model,
                max_tokens=self.max_tokens,
                messages=self.history,
                tools=self.tools,
                temperature=self.client.temperature,
                top_p=self.client.top_p,
                top_k=self.client.top_k,
                stop_sequences=self.client.stop_sequences,
                stream=self.is_stream)

        if self.is_stream:
            try:
                event = next(self.current_response)
                self._process_event(event)
            except StopIteration:
                self._finalize_initial_response()
        else:
            for content in self.current_response.content:
                if content.type == 'text':
                    self.assistant_message += content.text
                    self.buffer.append(content.text)
                elif content.type == 'tool_calls':
                    self.tool_uses.extend(content.tool_calls)
            self._finalize_initial_response()

    def _finalize_initial_response(self):
        self.initial_response_complete = True
        self.history.append({
            "role": "assistant",
            "content": self.assistant_message
        })
        if self.tool_uses:
            logger.debug(f"Tool uses found: {self.tool_uses}")
            self.state = 'tool_calls'
        else:
            logger.debug(
                "No tool uses found, transitioning to final_response state")
            self.state = 'final_response'
        self.current_response = None

    def _handle_tool_calls(self):
        if self.tool_uses:
            tool_call = self.tool_uses.pop(0)
            function_args = None
            function_name = tool_call.name
            try:
                if not tool_call.input:
                    function_args = {}
                else:
                    function_args = json.loads(tool_call.input)
            except AttributeError:
                logger.error(f"Unexpected tool_call structure: {tool_call}")
                function_name = "unknown"
                function_args = {}

            logger.debug(f"Handling tool call: {function_name}")

            if hasattr(self.function_module, function_name):
                function = getattr(self.function_module, function_name)
                try:
                    tool_result = function(**function_args)
                    tool_result = self.client.process_tool_result(tool_result)
                except Exception as e:
                    tool_result = f"Error executing {function_name}: {str(e)}"
            else:
                tool_result = f"Function {function_name} not found in the provided module."

            tool_result_message = f"\n使用工具: {function_name}\n参数: {function_args}\n工具结果: {tool_result}\n"
            self.history.append({
                "role": "user",
                "content": tool_result_message
            })
            self.buffer.append(tool_result_message)
        else:
            logger.debug(
                "No more tool calls, transitioning to final_response state")
            self.state = 'final_response'

    def _handle_final_response(self):
        if not self.current_response:
            self.current_response = self.client.client.messages.create(
                model=self.client.model,
                max_tokens=self.max_tokens,
                messages=self.history,
            temperature=self.client.temperature,
            top_p=self.client.top_p,
            top_k=self.client.top_k,
            stop_sequences=self.client.stop_sequences,
                stream=self.is_stream)

        if self.is_stream:
            try:
                event = next(self.current_response)
                self._process_event(event)
            except StopIteration:
                logger.debug(
                    "Final response complete, transitioning to finished state")
                self.state = 'finished'
        else:
            content = "".join([
                c.text for c in self.current_response.content
                if c.type == 'text'
            ])
            self.buffer.append(content)
            logger.debug(
                "Final response complete, transitioning to finished state")
            self.state = 'finished'

    def _process_event(self, event):
        logger.debug(f"Processing event of type: {event.type}")
        if event.type == 'content_block_start':
            if event.content_block.type == 'tool_use':
                logger.debug(f"Tool use detected: {event.content_block.name}")
                self.tool_uses.append(event.content_block)
        elif event.type == 'content_block_delta':
            if event.delta.type == 'text_delta':
                self.assistant_message += event.delta.text
                self.buffer.append(event.delta.text)
            elif event.delta.type == 'tool_calls':
                for tool_call in event.delta.tool_calls:
                    logger.debug(f"Adding tool call: {tool_call.name}")
                    self.tool_uses.append(tool_call)
        elif event.type == 'message_delta':
            if hasattr(event.delta, 'tool_calls'):
                for tool_call in event.delta.tool_calls:
                    logger.debug(
                        f"Adding tool call from message_delta: {tool_call.name}"
                    )
                    self.tool_uses.append(tool_call)
        elif event.type == 'message_stop':
            if not self.initial_response_complete:
                self._finalize_initial_response()



