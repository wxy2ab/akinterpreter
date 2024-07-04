from typing import List, Dict, Any, Optional
from anthropic import AnthropicBedrock
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
                 model: str = "anthropic.claude-3-5-sonnet-20240620-v1:0"):
        self.aws_region = aws_region
        self.model = model
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.aws_session_token = aws_session_token
        self.client = self._create_client()
        self.history: List[dict] = []
        self.stat: Dict[str, Any] = {
            "call_count": {"text_chat": 0, "image_chat": 0, "tool_chat": 0, "pdf_chat": 0},
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost": 0  # 如果可能的话，您可能想要根据实际定价计算成本
        }
        self.supported_sizes = [
            (1092, 1092), (951, 1268), (896, 1344), (819, 1456), (784, 1568)
        ]

    def _get_aws_credentials(self):
        from ..utils.config_setting import Config
        config = Config()
        if config.has_key("aws_access_key_id") and config.has_key("aws_secret_access_key"):
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
        
        raise ValueError("AWS credentials not found. Please provide credentials or configure your environment.")

    def _create_client(self):
        credentials = self._get_aws_credentials()
        return AnthropicBedrock(
            aws_access_key=credentials["aws_access_key"],
            aws_secret_key=credentials["aws_secret_key"],
            aws_session_token=credentials["aws_session_token"],
            aws_region=self.aws_region
        )

    def _update_usage_stats(self, response):
        usage = response.usage
        self.stat["total_input_tokens"] += usage.input_tokens
        self.stat["total_output_tokens"] += usage.output_tokens
        # 如果 API 提供了成本信息，您可以在这里更新总成本
        # self.stat["total_cost"] += usage.cost

    def text_chat(self, message: str, max_tokens: int = 10240) -> str:
        self.history.append({"role": "user", "content": message})
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=self.history
        )
        assistant_message = response.content[0].text
        self.history.append({"role": "assistant", "content": assistant_message})
        self.stat["call_count"]["text_chat"] += 1
        self._update_usage_stats(response)
        return assistant_message
    
    def one_chat(self, message: str, max_tokens: int = 10240) -> str:
        msg=[]
        msg.append({"role": "user", "content": message})
        @retry(3)
        def send_message():
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=msg
            )
            return response
        response = send_message()
        assistant_message = response.content[0].text
        msg.append({"role": "assistant", "content": assistant_message})
        self.stat["call_count"]["text_chat"] += 1
        self._update_usage_stats(response)
        return assistant_message
    
    def image_chat(self, message: str, image_url: str, max_tokens: int = 10240) -> str:
        image_message = {
            "role": "user", 
            "content": [
                {"type": "image", "source": {"type": "url", "url": image_url}},
                {"type": "text", "text": message}
            ]
        }
        self.history.append(image_message)
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=self.history
        )
        assistant_message = response.content[0].text
        self.history.append({"role": "assistant", "content": assistant_message})
        self.stat["call_count"]["image_chat"] += 1
        self._update_usage_stats(response)
        return assistant_message

    def image64_chat(self, message: str, image_path: str, max_tokens: int = 10240) -> str:
        # 读取并调整图片大小
        with Image.open(image_path) as img:
            resized_img = self._resize_image(img)
            resized_img.format = img.format  # 保留原始格式
            
            # 将调整后的图片转换为 base64
            buffered = io.BytesIO()
            resized_img.save(buffered, format=resized_img.format)
            base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

        # 构建消息
        image_message = {
            "role": "user", 
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": self._get_media_type(image_path), "data": base64_image}},
                {"type": "text", "text": message}
            ]
        }
        self.history.append(image_message)

        # 调用 Claude API
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=self.history
        )

        assistant_message = response.content[0].text
        self.history.append({"role": "assistant", "content": assistant_message})
        self.stat["call_count"]["image_chat"] += 1
        self._update_usage_stats(response)
        return assistant_message

    def _resize_image(self, img: Image.Image) -> Image.Image:
        original_width, original_height = img.size
        original_aspect_ratio = original_width / original_height

        # 找到最接近原始宽高比的支持尺寸
        closest_size = min(self.supported_sizes, 
                           key=lambda size: abs(size[0]/size[1] - original_aspect_ratio))

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
    
    def process_tool_result(self , tool_result):
        if isinstance(tool_result, str):
            try:
                return json.loads(tool_result)
            except json.JSONDecodeError:
                return tool_result
        return tool_result
    
    def tool_chat(self, user_message: str, tools: List[Dict[str, Any]], function_module: Any, max_tokens: int = 1000) -> str:
        # 移除工具描述中的 output_schema（如果存在）
        cleaned_tools = []
        for tool in tools:
            cleaned_tool = tool.copy()
            # pop 方法会安全地移除 output_schema，如果它不存在，则返回 None
            cleaned_tool.pop('output_schema', None)
            cleaned_tools.append(cleaned_tool)
        tools = cleaned_tools
        self.history.append({"role": "user", "content": user_message})
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=self.history,
            tools=tools
        )
        
        assistant_message = ""
        tool_uses = []

        for content in response.content:
            if content.type == 'text':
                assistant_message += content.text
            elif content.type == 'tool_use':
                tool_uses.append(content)

        self.history.append({"role": "assistant", "content": assistant_message})
        self._update_usage_stats(response)

        function_call_str=""

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

                self.history.append({"role": "user", "content": f"工具函数返回结果{function_name}: {tool_result}"})
                function_call_str = f"*使用工具*:{function_name}\n*参数:* {function_args} \n*工具结果:*{tool_result}"

            final_response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=self.history
            )
            final_assistant_message = "".join([content.text for content in final_response.content if content.type == 'text'])
            self.history.append({"role": "assistant", "content": final_assistant_message})
            self.stat["call_count"]["tool_chat"] += 1
            self._update_usage_stats(final_response)
            final_assistant_message = f"*首轮消息：*{assistant_message}\n{function_call_str}\n*最终结果：*{final_assistant_message}"
            return final_assistant_message
        else:
            self.stat["call_count"]["tool_chat"] += 1
            return assistant_message

    def one_tool_chat(self, user_message: str, tools: List[Dict[str, Any]], function_module: Any, max_tokens: int = 10000) -> str:
        # 移除工具描述中的 output_schema（如果存在）
        cleaned_tools = []
        for tool in tools:
            cleaned_tool = tool.copy()
            # pop 方法会安全地移除 output_schema，如果它不存在，则返回 None
            cleaned_tool.pop('output_schema', None)
            cleaned_tools.append(cleaned_tool)
        tools = cleaned_tools
        history=[]
        history.append({"role": "user", "content": user_message})
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=history,
            tools=tools
        )
        
        assistant_message = ""
        tool_uses = []

        for content in response.content:
            if content.type == 'text':
                assistant_message += content.text
            elif content.type == 'tool_use':
                tool_uses.append(content)

        
        history.append({"role": "assistant", "content": assistant_message})
        self._update_usage_stats(response)

        function_call_str=""

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

                history.append({"role": "user", "content": f"工具函数返回结果{function_name}: {tool_result}"})
                function_call_str = f"*使用工具*:{function_name}\n*参数:* {function_args} \n*工具结果:*{tool_result}"

            final_response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=history
            )
            final_assistant_message = "".join([content.text for content in final_response.content if content.type == 'text'])
            history.append({"role": "assistant", "content": final_assistant_message})
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
        raise NotImplementedError("Video chat is not supported in this version of Claude API client.")
    
    def audio_chat(self, message: str, audio_path: str) -> str:
        raise NotImplementedError("Audio chat is not supported in this version of Claude API client.")