import ast
import contextlib
import io
import json
from typing import Any, Dict, List, Union, Iterator
from openai import AzureOpenAI
import os
from ._llm_api_client import LLMApiClient
from ..utils.config_setting import Config
from ..utils.log import logger

logger.setLevel("ERROR")

class SimpleAzureClient(LLMApiClient):
    def __init__(self, 
                 api_key: str = None,
                 azure_endpoint: str = None,
                 max_tokens: int = 4000,
                 deployment_name: str = "gpt-4o",
                 api_version: str = "2023-05-15"):
        config = Config()
        
        self.api_key = api_key or config.get("AZURE_OPENAI_API_KEY")
        self.azure_endpoint = azure_endpoint or config.get("AZURE_OPENAI_ENDPOINT")
        self.deployment_name = deployment_name
        self.api_version = api_version
        self.max_tokens = max_tokens
        self.client = self._create_client()
        self.history: List[dict] = []
        self.stat: Dict[str, Any] = {
            "call_count": {"text_chat": 0, "image_chat": 0, "tool_chat": 0},
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost": 0
        }

    def _create_client(self):
        if not self.api_key or not self.azure_endpoint:
            raise ValueError("Azure OpenAI API key and endpoint are required.")
        return AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.azure_endpoint
        )

    def _update_usage_stats(self, response):
        if hasattr(response, 'usage'):
            usage = response.usage
            self.stat["total_input_tokens"] += usage.prompt_tokens
            self.stat["total_output_tokens"] += usage.completion_tokens
            self.stat["total_cost"] += usage.completion_tokens + usage.completion_tokens
            # Cost calculation would depend on your specific Azure pricing

    def _handle_streaming_response(self, response) -> Iterator[str]:
        full_response = ""
        for chunk in response:
            text =  chunk.choices[0].delta.content if chunk.choices[0].delta.content else ''
            full_response += text
            yield text
        self.history.append({"role": "assistant", "content": full_response})


    def text_chat(self, message: str, is_stream: bool = False) -> Union[str, Iterator[str]]:
        self.history.append({"role": "user", "content": message})
        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=self.history,
            max_tokens=self.max_tokens,
            stream=is_stream
        )
        self._update_usage_stats(response)
        if is_stream:
            return self._handle_streaming_response(response)
        else:
            text_response = response.choices[0].message.content
            self.history.append({"role": "assistant", "content": text_response})
            return text_response

    def one_chat(self, message: Union[str, List[Union[str, Any]]], is_stream: bool = False) -> Union[str, Iterator[str]]:
        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=message if isinstance(message, list) else [{"role": "user", "content": message}],
            max_tokens=self.max_tokens,
            stream=is_stream
        )
        self._update_usage_stats(response)
        if is_stream:
            return self._handle_streaming_response(response)
        else:
            return response.choices[0].message.content

    def tool_chat(self, user_message: str, tools: List[Dict[str, Any]], function_module: Any, is_stream: bool = False) -> Union[str, Iterator[str]]:
        self.history.append({"role": "user", "content": user_message})
        if is_stream:
            return self._unified_tool_stream(self.history, tools, function_module)
        else:
            response = self._create_chat_completion(self.history, is_stream, tools)
            return self._process_tool_response(response, tools, function_module)

    def _unified_tool_stream(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]], function_module: Any) -> Iterator[str]:
        response_stream = self._create_chat_completion(messages, True, tools, raw_response=True)
        full_response = ""
        current_tool_call = None
        tool_calls = []

        for chunk in response_stream:
            logger.debug(f"Received chunk: {chunk}")
            if chunk.choices and chunk.choices[0].delta:
                delta = chunk.choices[0].delta
                if delta.content:
                    logger.debug(f"Content received: {delta.content}")
                    yield delta.content
                    full_response += delta.content
                if delta.tool_calls:
                    logger.debug(f"Tool calls received: {delta.tool_calls}")
                    for tool_call in delta.tool_calls:
                        if tool_call.index is not None:
                            if tool_call.index >= len(tool_calls):
                                current_tool_call = {
                                    "id": tool_call.id or "",
                                    "type": tool_call.type or "function",
                                    "function": {
                                        "name": tool_call.function.name if tool_call.function else "",
                                        "arguments": tool_call.function.arguments if tool_call.function else ""
                                    }
                                }
                                tool_calls.append(current_tool_call)
                            else:
                                current_tool_call = tool_calls[tool_call.index]
                            
                            if tool_call.function:
                                if tool_call.function.name:
                                    current_tool_call["function"]["name"] = tool_call.function.name
                                if tool_call.function.arguments:
                                    current_tool_call["function"]["arguments"] += tool_call.function.arguments

        logger.debug(f"Full response: {full_response}")
        logger.debug(f"Tool calls: {tool_calls}")

        if tool_calls:
            yield "\n正在调用工具获取信息...\n"
            tool_outputs = self._execute_tool_calls(tool_calls, function_module)
            tool_results = []
            for tool_output in tool_outputs:
                result = self._format_tool_output(tool_output)
                tool_results.append(result)
                yield result

            tool_result_message = "\n".join(tool_results)
            messages.append({"role": "assistant", "content": f"{full_response}\n\n工具调用结果:\n{tool_result_message}"})
            
            yield "\n正在分析工具调用结果...\n"
            explanation_request = "请根据上述工具调用的结果，提供一个简洁明了的回答。"
            messages.append({"role": "user", "content": explanation_request})
            
            explanation_stream = self._create_chat_completion(messages, True, tools, raw_response=True)
            for chunk in explanation_stream:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        elif full_response.strip():
            yield f"\n{full_response}\n"
        else:
            yield "\n无法生成回答。请尝试重新提问。\n"

        self.history = messages[-5:]

    def _format_tool_output(self, tool_output: Dict[str, str]) -> str:
        tool_name = tool_output['name']
        content = tool_output['content']
        
        formatted_output = f"\n工具 '{tool_name}' 的调用结果:\n"
        formatted_output += "-" * 40 + "\n"
        
        try:
            # 尝试将内容解析为 JSON
            content_dict = json.loads(content)
            for key, value in content_dict.items():
                formatted_output += f"{key}: {value}\n"
        except json.JSONDecodeError:
            # 如果不是 JSON，就按原样输出
            formatted_output += content

        formatted_output += "\n"
        formatted_output += "-" * 40 + ""
        return formatted_output

    def _create_chat_completion(self, messages: List[Dict[str, str]], is_stream: bool, tools: List[Dict[str, Any]] = None, raw_response: bool = False) -> Union[str, Iterator[str]]:
        kwargs = {
            "model": self.deployment_name,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "stream": is_stream
        }
        if tools:
            kwargs["tools"] = tools

        completion = self.client.chat.completions.create(**kwargs)
        if is_stream:
            return completion if raw_response else self._handle_streaming_response(completion)
        else:
            response = completion.choices[0].message.content
            self._update_usage_stats(completion)
            return response

    def _process_tool_response(self, response, tools: List[Dict[str, Any]], function_module: Any) -> str:
        assistant_output = response.choices[0].message
        self._update_usage_stats(response)

        if hasattr(assistant_output, 'tool_calls') and assistant_output.tool_calls:
            self.history.append({"role": "assistant", "content": assistant_output.content, "tool_calls": assistant_output.tool_calls})
            tool_outputs = self._execute_tool_calls(assistant_output.tool_calls, function_module)
            self.history.extend(tool_outputs)
            second_response = self._create_chat_completion(self.history, False, tools)
            final_output = second_response
        else:
            self.history.append({"role": "assistant", "content": assistant_output.content})
            final_output = assistant_output.content

        return final_output

    def _execute_tool_calls(self, tool_calls, function_module: Any) -> List[Dict[str, str]]:
        tool_outputs = []
        for tool_call in tool_calls:
            tool_name = tool_call["function"]["name"]
            try:
                tool_args = json.loads(tool_call["function"]["arguments"])
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse arguments for tool {tool_name}: {tool_call['function']['arguments']}")
                tool_args = {}
            
            if hasattr(function_module, tool_name):
                tool_func = getattr(function_module, tool_name)
                try:
                    tool_output = tool_func(**tool_args)
                    tool_outputs.append({
                        "role": "function",
                        "name": tool_name,
                        "content": str(tool_output),
                        "tool_call_id": tool_call["id"]
                    })
                except Exception as e:
                    error_message = f"Error executing {tool_name}: {str(e)}"
                    logger.error(error_message, exc_info=True)
                    tool_outputs.append({
                        "role": "function",
                        "name": tool_name,
                        "content": error_message,
                        "tool_call_id": tool_call["id"]
                    })
            else:
                error_message = f"Error: Function {tool_name} not found."
                logger.error(error_message)
                tool_outputs.append({
                    "role": "function",
                    "name": tool_name,
                    "content": error_message,
                    "tool_call_id": tool_call["id"]
                })

        return tool_outputs

    def get_history(self) -> List[Dict[str, Any]]:
        return self.history

    def clear_chat(self) -> None:
        self.history.clear()

    def get_stats(self) -> Dict[str, int]:
        return self.stat
    
    def audio_chat(self, message: str, audio_path: str) -> str:
        raise NotImplementedError("Azure OpenAI does not support audio input.")
    
    def video_chat(self, message: str, video_path: str) -> str:
        raise NotImplementedError("Azure OpenAI does not support video input.")

    def image_chat(self, message: str, image_path: str) -> str:
        raise NotImplementedError("Image chat is not implemented for SimpleAzureClient.")