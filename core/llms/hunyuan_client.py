import json
import types
from typing import Any, Dict, Iterator, List, Union
from abc import ABC, abstractmethod
from core.llms._llm_api_client import LLMApiClient
# 腾讯云sdk pip install tencentcloud-sdk-python
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.hunyuan.v20230901 import hunyuan_client, models
from ..utils.config_setting import Config
from ..utils.handle_max_tokens import handle_max_tokens

class HunyuanClient(LLMApiClient):
    # Tencent Hunyuan ChatCompletions API does not document a ResponseFormat
    # parameter (https://cloud.tencent.com/document/product/1729/105701).
    # See core/ccx/docs/role_based_llm_routing.md §7.1 capability matrix.
    supports_structured_output = False

    def __init__(self):
        try:
            config = Config()
            secret_id = config.get("hunyuan_SecretId")
            secret_key = config.get("hunyuan_SecretKey")
            self.cred = credential.Credential(secret_id, secret_key)
            self.httpProfile = HttpProfile()
            self.httpProfile.endpoint = "hunyuan.tencentcloudapi.com"
            self.clientProfile = ClientProfile()
            self.clientProfile.httpProfile = self.httpProfile
            self.client = hunyuan_client.HunyuanClient(self.cred, "", self.clientProfile)
            self.history = []
            self.model = "hunyuan-pro"
        except Exception as err:
            print(f"初始化错误: {err}")

    def set_system_message(self, system_message: str = "你是一个智能助手,擅长把复杂问题清晰明白通俗易懂地解答出来"):
        if not hasattr(self, "history"):
            self.history = []
        self.history = [{"Role": "system", "Content": system_message}]
    #@handle_max_tokens
    def text_chat(self, message: str, is_stream: bool = False) -> Union[str, Iterator[str]]:
        self.history.append({"Role": "user", "Content": message})
        req = models.ChatCompletionsRequest()
        params = {
            "Messages": self.history,
            "Stream": is_stream,
            "Model": self.model
        }
        req.from_json_string(json.dumps(params))

        response = self._process_response(req, is_stream)
        if is_stream:
            return self._iterate_stream_response(response)
        return response

    def _iterate_stream_response(self, response: Iterator[str]) -> Iterator[str]:
        for chunk in response:
            yield chunk

    def tool_chat(self, user_message: str, tools: List[Dict[str, Any]], function_module: Any, is_stream: bool = False) -> Union[str, Iterator[str]]:
        self.history.append({"Role": "user", "Content": user_message})
        req = models.ChatCompletionsRequest()
        params = {
            "Messages": self.history,
            "Stream": is_stream,
            "Model": "hunyuan-functioncall",
            "Tools": tools,
            "ToolChoice": "auto"
        }
        req.from_json_string(json.dumps(params))

        try:
            resp = self.client.ChatCompletions(req)

            if is_stream:
                return self._stream_tool_response(resp, function_module)
            else:
                return self._non_stream_tool_response(resp, function_module)

        except TencentCloudSDKException as err:
            return f"Error: {str(err)}"

    def _stream_tool_response(self, resp: types.GeneratorType, function_module: Any) -> Iterator[str]:
        current_response = ""
        for event in resp:
            if 'Choices' in event and event['Choices']:
                delta = event['Choices'][0].get('Delta', {})
                content = delta.get('Content', '')
                tool_calls = delta.get('ToolCalls', [])

                if content:
                    current_response += content
                    yield content

                if tool_calls:
                    for call in tool_calls:
                        if call['Type'] == 'function':
                            func_name = call['Function']['Name']
                            func_args = json.loads(call['Function']['Arguments'])
                            if hasattr(function_module, func_name):
                                func = getattr(function_module, func_name)
                                result = func(**func_args)
                                tool_response = {
                                    "Role": "tool",
                                    "ToolCallId": call['Id'],
                                    "Content": json.dumps(result)
                                }
                                self.history.append(tool_response)
                                yield f"Tool call: {func_name}\nResult: {json.dumps(result)}\n"

        self.history.append({"Role": "assistant", "Content": current_response})

    def _non_stream_tool_response(self, resp: models.ChatCompletionsResponse, function_module: Any) -> str:
        response = resp.Choices[0].Message.Content
        tool_calls = resp.Choices[0].Message.ToolCalls

        if tool_calls:
            for call in tool_calls:
                if call.Type == 'function':
                    func_name = call.Function.Name
                    func_args = json.loads(call.Function.Arguments)
                    if hasattr(function_module, func_name):
                        func = getattr(function_module, func_name)
                        result = func(**func_args)
                        tool_response = {
                            "Role": "tool",
                            "ToolCallId": call.Id,
                            "Content": json.dumps(result)
                        }
                        self.history.append(tool_response)

            # 再次调用API获取最终响应
            req = models.ChatCompletionsRequest()
            retry_params: Dict[str, Any] = {
                "Messages": self.history,
                "Stream": False,
                "Model": "hunyuan-functioncall",
                "Tools": [],
                "ToolChoice": "none",
            }
            req.from_json_string(json.dumps(retry_params))
            final_resp = self.client.ChatCompletions(req)
            final_response = final_resp.Choices[0].Message.Content
            self.history.append({"Role": "assistant", "Content": final_response})
            return final_response
        
        self.history.append({"Role": "assistant", "Content": response})
        return response

    def tool_invoke(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        req = models.ChatCompletionsRequest()
        normalized_messages = [
            {"Role": message.get("role", "user"), "Content": message.get("content", "")}
            for message in messages
        ]
        invoke_params: Dict[str, Any] = {
            "Messages": normalized_messages,
            "Stream": False,
            "Model": "hunyuan-functioncall",
            "Tools": tools,
            "ToolChoice": "auto",
        }
        req.from_json_string(json.dumps(invoke_params))
        resp = self.client.ChatCompletions(req)
        message = resp.Choices[0].Message
        content = getattr(message, "Content", "") or ""
        tool_calls = []
        for call in getattr(message, "ToolCalls", []) or []:
            if call.Type == "function":
                tool_calls.append({
                    "id": call.Id,
                    "function": {
                        "name": call.Function.Name,
                        "arguments": call.Function.Arguments
                    }
                })
        return self._normalize_tool_invoke_response(content, tool_calls)

    def audio_chat(self, message: str, audio_path: str) -> str:
        raise NotImplementedError("Hunyuan API does not support audio chat")

    def video_chat(self, message: str, video_path: str) -> str:
        raise NotImplementedError("Hunyuan API does not support video chat")

    def clear_chat(self):
        self.history = []

    def one_chat(self, message: Union[str, List[Union[str, Any]]], is_stream: bool = False) -> Union[str, Iterator[str]]:
        # Store the original history
        original_history = self.history.copy()
        
        # Clear the history for this one-time chat
        self.history = []
        
        try:
            req = models.ChatCompletionsRequest()
            params = {
                "Messages": [{"Role": "user", "Content": message}] if isinstance(message, str) else message,
                "Stream": is_stream,
                "Model": self.model
            }
            req.from_json_string(json.dumps(params))

            return self._process_response(req, is_stream, use_history=False)
        finally:
            # Restore the original history
            self.history = original_history

    def get_stats(self) -> Dict[str, Any]:
        return {"token_usage": "Not available", "api_calls": "Not available"}

    def _process_response(self, req: models.ChatCompletionsRequest, is_stream: bool, use_history: bool = True) -> Union[str, Iterator[str]]:
        try:
            resp = self.client.ChatCompletions(req)
            if is_stream and isinstance(resp, types.GeneratorType):
                return self._stream_response(resp, use_history)
            elif not is_stream:
                return self._non_stream_response(resp, use_history)
            else:
                raise ValueError("Unexpected response type")
        except TencentCloudSDKException as err:
            return f"Error: {str(err)}"

    def _stream_response(self, resp: types.GeneratorType, use_history: bool = True) -> Iterator[str]:
        try:
            for event in resp:
                if isinstance(event, dict) and 'data' in event:
                    try:
                        data = json.loads(event['data'])
                        if 'Choices' in data and data['Choices']:
                            delta = data['Choices'][0].get('Delta', {})
                            content = delta.get('Content', '')
                            if content:
                                if use_history:
                                    self.history.append({"Role": "assistant", "Content": content})
                                yield content
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            raise

    def _non_stream_response(self, resp: Union[models.ChatCompletionsResponse, types.GeneratorType], use_history: bool = True) -> str:
        if isinstance(resp, types.GeneratorType):
            content = "".join(chunk for chunk in resp if 'Choices' in chunk and chunk['Choices'])
        else:
            content = resp.Choices[0].Message.Content
        if use_history:
            self.history.append({"Role": "assistant", "Content": content})
        return content

    def _handle_tool_calls(self, response: str, function_module: Any):
        tool_calls = json.loads(response).get('ToolCalls', [])
        for call in tool_calls:
            if call['Type'] == 'function':
                func_name = call['Function']['Name']
                func_args = json.loads(call['Function']['Arguments'])
                if hasattr(function_module, func_name):
                    func = getattr(function_module, func_name)
                    result = func(**func_args)
                    self.history.append({
                        "Role": "tool",
                        "ToolCallId": call['Id'],
                        "Content": json.dumps(result)
                    })
        self.history.append({"Role": "assistant", "Content": response})
