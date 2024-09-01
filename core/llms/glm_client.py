from typing import List, Dict, Any, Literal, Union, Iterator
from zhipuai import ZhipuAI
import json
from ._llm_api_client import LLMApiClient
from ..utils.config_setting import Config
from ..utils.handle_max_tokens import handle_max_tokens

class GLMClient(LLMApiClient):
    def __init__(self, api_key: str = "", model: Literal["glm-4-0520", "glm-4", "glm-4-air", "glm-4-airx", "glm-4-flash","glm-4-long"] = "glm-4-plus",
                 do_sample: bool = False, temperature: float = 0.95, top_p: float = 0.7, max_tokens: int = 4000, stop: Union[str, List[str], None] = None):
        config = Config()
        if api_key == "" and config.has_key("glm_api_key"):
            api_key = config.get("glm_api_key")
        self.client = ZhipuAI(api_key=api_key)
        self.model = model
        self.image_model =  "glm-4v-plus"
        self.history = []
        self.do_sample = do_sample
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        self.stop = stop

    def set_system_message(self, system_message: str = "你是一个智能助手,擅长把复杂问题清晰明白通俗易懂地解答出来"):
        self.history = [{"role": "system", "content": system_message}]
    @handle_max_tokens
    def text_chat(self, message: str, is_stream: bool = False) -> Union[str, Iterator[str]]:
        if not self.history:
            self.set_system_message()
        self.history.append({"role": "user", "content": message})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.history,
            do_sample=self.do_sample,
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_tokens,
            stop=self.stop,
            stream=is_stream
        )
        
        if is_stream:
            def generate():
                full_response = ""
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
                        full_response += chunk.choices[0].delta.content
                self.history.append({"role": "assistant", "content": full_response})
            return generate()
        else:
            output = response.choices[0].message.content
            self.history.append({"role": "assistant", "content": output})
            return output

    def one_chat(self, message: Union[str, List[Union[str, Dict[str, str]]]], is_stream: bool = False) -> Union[str, Iterator[str]]:
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

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            do_sample=self.do_sample,
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_tokens,
            stop=self.stop,
            stream=is_stream
        )
        
        if is_stream:
            return self._handle_stream_response(response)
        else:
            return response.choices[0].message.content
    
    def _handle_stream_response(self, response) -> Iterator[str]:
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def tool_chat(self, user_message: str, tools: List[Dict[str, Any]], function_module: Any, is_stream: bool = False) -> Union[str, Iterator[str]]:
        self.history.append({"role": "user", "content": user_message})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.history,
            tools=tools,
            tool_choice="auto",
            do_sample=self.do_sample,
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_tokens,
            stop=self.stop,
            stream=is_stream
        )
        
        if is_stream:
            return self._stream_tool_chat(response, tools, function_module)
        else:
            return self._non_stream_tool_chat(response, tools, function_module)

    def _stream_tool_chat(self, response, tools: List[Dict[str, Any]], function_module: Any) -> Iterator[str]:
        full_response = ""
        tool_calls = []
        
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta:
                delta = chunk.choices[0].delta
                
                if delta.content is not None:
                    yield delta.content
                    full_response += delta.content
                
                if hasattr(delta, 'tool_calls') and delta.tool_calls:
                    for tool_call in delta.tool_calls:
                        if tool_call.index >= len(tool_calls):
                            tool_calls.append({
                                "id": tool_call.id,
                                "type": "function",
                                "function": {
                                    "name": tool_call.function.name,
                                    "arguments": tool_call.function.arguments
                                }
                            })
                        else:
                            # 更新已存在的tool_call
                            tool_calls[tool_call.index]["function"]["arguments"] += tool_call.function.arguments
        
        if tool_calls:
            if not full_response:
                full_response = f"我将调用工具:{tool_calls[0]["function"]["name"]}"
            assistant_message = {
                "role": "assistant",
                "content": full_response,
                "tool_calls": tool_calls
            }
            self.history.append(assistant_message)
            
            yield "\n执行工具调用...\n"
            for tool_call in tool_calls:
                tool_name = tool_call["function"]["name"]
                tool_args = json.loads(tool_call["function"]["arguments"])
                
                if hasattr(function_module, tool_name):
                    tool_func = getattr(function_module, tool_name)
                    try:
                        tool_output = tool_func(**tool_args)
                        yield f"工具 {tool_call['id']} 返回结果: {tool_output}\n"
                        tool_msg = {"role": "tool", "content": str(tool_output), "tool_call_id": tool_call["id"]}
                        self.history.append(tool_msg)
                    except Exception as e:
                        error_msg = f"Error executing {tool_name}: {str(e)}"
                        yield f"工具 {tool_call['id']} 执行错误: {error_msg}\n"
                        tool_msg = {"role": "tool", "content": error_msg, "tool_call_id": tool_call["id"]}
                        self.history.append(tool_msg)
                else:
                    error_msg = f"Function {tool_name} not found in the provided module."
                    yield f"工具 {tool_call['id']} 未找到: {error_msg}\n"
                    tool_msg = {"role": "tool", "content": error_msg, "tool_call_id": tool_call["id"]}
                    self.history.append(tool_msg)
            
            yield "\n生成最终回复...\n"
            final_response = self.client.chat.completions.create(
                model=self.model,
                messages=self.history,
                do_sample=self.do_sample,
                temperature=self.temperature,
                top_p=self.top_p,
                max_tokens=self.max_tokens,
                stop=self.stop,
                stream=True
            )
            
            for chunk in final_response:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        else:
            self.history.append({"role": "assistant", "content": full_response})

    def _non_stream_tool_chat(self, response, tools: List[Dict[str, Any]], function_module: Any) -> str:
        output = response.choices[0].message
        full_response = output.content or ""
        tool_calls = []

        if hasattr(output, 'tool_calls'):
            for tool_call in output.tool_calls:
                tool_calls.append({
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    }
                })

        assistant_message = {
            "role": "assistant",
            "content": full_response,
            "tool_calls": tool_calls
        }
        self.history.append(assistant_message)

        if tool_calls:
            for tool_call in tool_calls:
                tool_name = tool_call["function"]["name"]
                tool_args = json.loads(tool_call["function"]["arguments"])
                
                if hasattr(function_module, tool_name):
                    tool_func = getattr(function_module, tool_name)
                    try:
                        tool_output = tool_func(**tool_args)
                        tool_msg = {"role": "tool", "content": str(tool_output), "tool_call_id": tool_call["id"]}
                        self.history.append(tool_msg)
                    except Exception as e:
                        error_msg = f"Error executing {tool_name}: {str(e)}"
                        tool_msg = {"role": "tool", "content": error_msg, "tool_call_id": tool_call["id"]}
                        self.history.append(tool_msg)
                else:
                    error_msg = f"Function {tool_name} not found in the provided module."
                    tool_msg = {"role": "tool", "content": error_msg, "tool_call_id": tool_call["id"]}
                    self.history.append(tool_msg)

            final_response = self.client.chat.completions.create(
                model=self.model,
                messages=self.history,
                do_sample=self.do_sample,
                temperature=self.temperature,
                top_p=self.top_p,
                max_tokens=self.max_tokens,
                stop=self.stop
            )
            final_output = final_response.choices[0].message.content
            self.history.append({"role": "assistant", "content": final_output})
            return final_output
        else:
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

    def clear_chat(self) -> None:
        self.history = []

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_messages": len(self.history)
        }

    def image_chat(self, message: str, image_path: str) -> str:
        raise NotImplementedError("GLM API does not support image chat.")

    def audio_chat(self, message: str, audio_path: str) -> str:
        raise NotImplementedError("GLM API does not support audio chat.")

    def video_chat(self, message: str, video_path: str) -> str:
        raise NotImplementedError("GLM API does not support video chat.")