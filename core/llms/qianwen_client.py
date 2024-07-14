import json
from http import HTTPStatus
from dashscope import Generation
from typing import Iterator, List, Dict, Any, Union
from ._llm_api_client import LLMApiClient
from ..utils.config_setting import Config

class QianWenClient(LLMApiClient):
    def __init__(self, api_key: str = "", max_tokens: int = 2000, top_p: float = 0.8, 
                 repetition_penalty: float = 1, temperature: float = 1, 
                 stop: Union[str, List[str], None] = None, enable_search: bool = False):
        import dashscope
        config = Config()
        if api_key == "" and config.has_key("DASHSCOPE_API_KEY"):
            api_key = config.get("DASHSCOPE_API_KEY")
        dashscope.api_key = api_key
        self.messages = [{'role': 'system', 'content': '你是一个智能助手。'}]
        self.total_tokens = 0
        self.request_count = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.models = ['qwen-max', 'qwen-plus', 'qwen-max-longcontext']
        self.model = self.models[0]
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.repetition_penalty = repetition_penalty
        self.temperature = temperature
        self.stop = stop
        self.enable_search = enable_search

    def text_chat(self, message: str, is_stream: bool = False) -> Union[str, Iterator[str]]:
        self.messages.append({'role': 'user', 'content': message})
        if is_stream:
            return self._stream_response(self.messages)
        else:
            response = self._send_request(self.messages, model=self.model)
            if response.status_code == HTTPStatus.OK:
                assistant_message = response.output.choices[0]['message']
                self.messages.append(assistant_message)
                return assistant_message['content']
            else:
                self.messages.pop()
                return "Error: Failed to get response from the model."

    def one_chat(self, message: str, is_stream: bool = False) -> Union[str, Iterator[str]]:
        messages = self.messages.copy()
        messages.append({'role': 'user', 'content': message})
        if is_stream:
            return self._stream_response(messages)
        else:
            response = self._send_request(messages, model=self.model)
            if response.status_code == HTTPStatus.OK:
                assistant_message = response.output.choices[0]['message']
                return assistant_message['content']
            else:
                return "Error: Failed to get response from the model."

    def tool_chat(self, user_message: str, tools: List[Dict[str, Any]], function_module: Any, is_stream: bool = False) -> Union[str, Iterator[str]]:
        self.messages.append({"role": "user", "content": user_message})
        
        if is_stream:
            return self._stream_tool_chat(tools, function_module)
        else:
            return self._non_stream_tool_chat(tools, function_module)

    def _non_stream_tool_chat(self, tools: List[Dict[str, Any]], function_module: Any) -> str:
        response = self._send_tool_request(self.messages, tools)
        
        if response.status_code != HTTPStatus.OK:
            self.messages.pop()
            return "Error: Failed to get response from the model."

        assistant_message = response.output.choices[0]['message']
        self.messages.append(assistant_message)
        
        if 'tool_calls' in assistant_message:
            tool_calls = assistant_message['tool_calls']
            for tool_call in tool_calls:
                function_name = tool_call['function']['name']
                try:
                    function_args = json.loads(tool_call['function']['arguments'])
                except json.JSONDecodeError:
                    function_args = {}

                tool_result = self._execute_function(function_name, function_args, function_module)
                
                self.messages.append({
                    "role": "tool",
                    "name": function_name,
                    "content": str(tool_result)
                })

            final_response = self._send_tool_request(self.messages, tools)
            if final_response.status_code == HTTPStatus.OK:
                final_message = final_response.output.choices[0]['message']
                self.messages.append(final_message)
                return final_message['content']
            else:
                return "Error: Failed to get final response from the model."
        else:
            return assistant_message['content']

    def _stream_tool_chat(self, tools: List[Dict[str, Any]], function_module: Any) -> Iterator[str]:
        response_stream = self._send_tool_request(self.messages, tools, stream=True)
        full_response = ""
        tool_calls = []

        for chunk in response_stream:
            if chunk.status_code == HTTPStatus.OK:
                content = chunk.output.choices[0]['message'].get('content', '')
                if content:
                    yield content
                    full_response += content
                
                if 'tool_calls' in chunk.output.choices[0]['message']:
                    for tool_call in chunk.output.choices[0]['message']['tool_calls']:
                        if tool_call['index'] >= len(tool_calls):
                            tool_calls.append({
                                "function": {"name": tool_call['function']['name'], "arguments": tool_call['function']['arguments']}
                            })
                        else:
                            tool_calls[tool_call['index']]['function']['arguments'] += tool_call['function']['arguments']
            else:
                yield f"Error: {chunk.code} - {chunk.message}"

        if tool_calls:
            for tool_call in tool_calls:
                function_name = tool_call['function']['name']
                try:
                    function_args = json.loads(tool_call['function']['arguments'])
                except json.JSONDecodeError:
                    function_args = {}

                tool_result = self._execute_function(function_name, function_args, function_module)
                yield f"\nTool Call: {function_name}\nTool Result: {tool_result}\n"

                self.messages.append({
                    "role": "tool",
                    "name": function_name,
                    "content": str(tool_result)
                })

            final_response_stream = self._send_tool_request(self.messages, tools, stream=True)
            for chunk in final_response_stream:
                if chunk.status_code == HTTPStatus.OK:
                    content = chunk.output.choices[0]['message'].get('content', '')
                    if content:
                        yield content
                else:
                    yield f"Error: {chunk.code} - {chunk.message}"
        
        self.messages.append({"role": "assistant", "content": full_response})

    def _execute_function(self, function_name: str, function_args: Dict[str, Any], function_module: Any) -> Any:
        if hasattr(function_module, function_name):
            function = getattr(function_module, function_name)
            try:
                return function(**function_args)
            except Exception as e:
                return f"Error executing {function_name}: {str(e)}"
        else:
            return f"Error: Function {function_name} not found in the provided module."

    def _send_tool_request(self, messages, tools, model="qwen-max", stream=False):
        self.request_count += 1
        response = Generation.call(
            model=model,
            messages=messages,
            tools=tools,
            result_format='message',
            stream=stream,
            incremental_output=stream,
            max_tokens=self.max_tokens,
            top_p=self.top_p,
            repetition_penalty=self.repetition_penalty,
            temperature=self.temperature,
            stop=self.stop,
            enable_search=self.enable_search
        )
        if not stream and response.status_code == HTTPStatus.OK:
            self.successful_requests += 1
            self.total_tokens += response.usage['total_tokens']
        elif not stream:
            self.failed_requests += 1
        return response

    def _send_request(self, messages, model="qwen-max"):
        self.request_count += 1
        response = Generation.call(
            model=model, 
            messages=messages,
            result_format='message',
            max_tokens=self.max_tokens,
            top_p=self.top_p,
            repetition_penalty=self.repetition_penalty,
            temperature=self.temperature,
            stop=self.stop,
            enable_search=self.enable_search
        )
        if response.status_code == HTTPStatus.OK:
            self.successful_requests += 1
            self.total_tokens += response.usage['total_tokens']
        else:
            self.failed_requests += 1
        return response

    def _stream_response(self, messages: List[Dict[str, str]]) -> Iterator[str]:
        responses = Generation.call(
            model=self.model,
            messages=messages,
            result_format='message',
            stream=True,
            incremental_output=True,
            max_tokens=self.max_tokens,
            top_p=self.top_p,
            repetition_penalty=self.repetition_penalty,
            temperature=self.temperature,
            stop=self.stop,
            enable_search=self.enable_search
        )
        full_response = ""
        for response in responses:
            if response.status_code == HTTPStatus.OK:
                text =  response.output.choices[0]['message']['content']
                full_response += text
                yield text
            else:
                yield f"Error: {response.code} - {response.message}"
        self.messages.append({"role": "assistant", "content": full_response})
        self.request_count += 1
        self.successful_requests += 1

    def _stream_tool_response(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]], function_module: Any) -> Iterator[str]:
        responses = Generation.call(
            model=self.model,
            messages=messages,
            tools=tools,
            result_format='message',
            stream=True,
            incremental_output=True,
            max_tokens=self.max_tokens,
            top_p=self.top_p,
            repetition_penalty=self.repetition_penalty,
            temperature=self.temperature,
            stop=self.stop,
            enable_search=self.enable_search
        )
        assistant_message = ""
        for response in responses:
            if response.status_code == HTTPStatus.OK:
                content = response.output.choices[0]['message']['content']
                assistant_message += content
                yield content
            else:
                yield f"Error: {response.code} - {response.message}"
        
        self.request_count += 1
        self.successful_requests += 1

        # 处理工具调用
        if 'tool_calls' in response.output.choices[0]['message']:
            tool_call = response.output.choices[0]['message']['tool_calls'][0]
            tool_name = tool_call['function']['name']
            tool_args = json.loads(tool_call['function']['arguments'])
            tool_args = tool_args["properties"]

            if hasattr(function_module, tool_name) and callable(getattr(function_module, tool_name)):
                tool_func = getattr(function_module, tool_name)
                tool_output = tool_func(**tool_args)
                yield f"\nTool Call: {tool_name}\nTool Output: {tool_output}\n"

                # 获取最终响应
                final_messages = messages + [
                    {'role': 'assistant', 'content': assistant_message},
                    {'role': 'tool', 'name': tool_name, 'content': str(tool_output)}
                ]
                for chunk in self._stream_response(final_messages):
                    yield chunk
            else:
                yield f"\nError: Function {tool_name} not found in the provided module."

    def _process_tool_response(self, response, tools, function_module):
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