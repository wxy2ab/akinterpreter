import json
from http import HTTPStatus
from dashscope import Generation
from typing import List, Dict, Any
from ._llm_api_client import LLMApiClient
from ..utils.config_setting import Config

class QianWenClient(LLMApiClient):
    def __init__(self ,api_key:str=""):
        import dashscope
        config  = Config()
        if api_key == "" and config.has_key("DASHSCOPE_API_KEY"):
            api_key = config.get("DASHSCOPE_API_KEY")
        dashscope.api_key = api_key
        self.messages = [{'role': 'system', 'content': '你是一个代码超人,写得一手好代码,格式规范,注释清晰,逻辑明确,代码易读,易于维护。'}]
        self.total_tokens = 0
        self.request_count = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.models = ['qwen-max', 'qwen-plus', 'qwen-max-longcontext']
        self.model = self.models[0]

    def text_chat(self, message: str) -> str:
        self.messages.append({'role': 'user', 'content': message})
        response = self._send_request(self.messages, model=self.model)
        if response.status_code == HTTPStatus.OK:
            assistant_message = response.output.choices[0]['message']
            self.messages.append(assistant_message)
            return assistant_message['content']
        else:
            self.messages.pop()
            return "Error: Failed to get response from the model."

    def one_chat(self, message: str) -> str:
        messages = self.messages.copy()
        messages.append({'role': 'user', 'content': message})
        response = self._send_request(messages, model=self.model)
        if response.status_code == HTTPStatus.OK:
            assistant_message = response.output.choices[0]['message']
            return assistant_message['content']
        else:
            return "Error: Failed to get response from the model."

    def tool_chat(self, user_message: str, tools: List[Dict[str, Any]], function_module: Any) -> str:
        self.messages.append({'role': 'user', 'content': user_message})
        response = self._send_tool_request(self.messages, tools)
        if response.status_code == HTTPStatus.OK:
            assistant_output = response.output.choices[0].message
            self.messages.append(assistant_output)
            
            if 'tool_calls' in assistant_output:
                tool_call = assistant_output.tool_calls[0]
                tool_name = tool_call['function']['name']
                tool_args = json.loads(tool_call['function']['arguments'])
                tool_args = tool_args["properties"]

                if hasattr(function_module, tool_name) and callable(getattr(function_module, tool_name)):
                    tool_func = getattr(function_module, tool_name)
                    tool_output = tool_func(**tool_args)
                    tool_msg = {"name": tool_name, "role": "tool", "content": tool_output}
                    self.messages.append(tool_msg)
                    
                    second_response = self._send_tool_request(self.messages, tools, model=self.model)
                    final_output = second_response.output.choices[0].message['content']
                    self.messages.append(second_response.output.choices[0].message)
                else:
                    final_output = f"Error: Function {tool_name} not found in the provided module."
            else:
                final_output = assistant_output['content']
                
            return final_output
        else:
            self.messages.pop()
            return "Error: Failed to get response from the model."

    def _send_request(self, messages, model="qwen-max"):
        self.request_count += 1
        response = Generation.call(model=model, 
                                   messages=messages,
                                   result_format='message')
        if response.status_code == HTTPStatus.OK:
            self.successful_requests += 1
            self.total_tokens += response.usage['total_tokens']
        else:
            self.failed_requests += 1
        return response

    def _send_tool_request(self, messages, tools, model="qwen-max"):
        self.request_count += 1
        response = Generation.call(model=model,
                                   messages=messages,
                                   tools=tools,
                                   result_format='message')
        if response.status_code == HTTPStatus.OK:
            self.successful_requests += 1
            self.total_tokens += response.usage['total_tokens']
        else:
            self.failed_requests += 1
        return response

    def get_stats(self) -> Dict[str, Any]:
        return {
            'total_tokens': self.total_tokens,
            'request_count': self.request_count,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests
        }

    def clear_chat(self) -> None:
        self.messages = [self.messages[0]]  # Keep the system message

    def image_chat(self, message: str, image_path: str) -> str:
        raise NotImplementedError("QianWen API does not support image chat.")

    def audio_chat(self, message: str, audio_path: str) -> str:
        raise NotImplementedError("QianWen API does not support audio chat.")

    def video_chat(self, message: str, video_path: str) -> str:
        raise NotImplementedError("QianWen API does not support video chat.")