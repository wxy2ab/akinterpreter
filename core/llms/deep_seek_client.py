from typing import Iterator, List, Dict, Any, Literal, Optional, Union
import openai
import json
from ._llm_api_client import LLMApiClient
from ..utils.config_setting import Config

class DeepSeekClient(LLMApiClient):
    def __init__(self, api_key: Optional[str] = None,max_tokens:int=4000, base_url: str = "https://api.deepseek.com/", model: Literal["deepseek-chat", "deepseek-coder"] = "deepseek-chat"
                 , temperature: float = 0.7,
                 top_p: float = 1.0, frequency_penalty: float = 0, presence_penalty: float = 0,
                 stop: Optional[Union[str, List[str]]] = None
                 ):
        config = Config()
        if api_key is None and config.has_key("deep_seek_api_key"):
            api_key = config.get("deep_seek_api_key")
        self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
        self.messages = []
        self.task = "通用对话"
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty
        self.stop = stop
        self.stats = {
            "total_tokens": 0,
            "completion_tokens": 0,
            "prompt_tokens": 0,
            "total_cost": 0.0,
            "num_chats": 0,
        }

    def _handle_streaming_response(self, response) -> Iterator[str]:
        full_response = ""
        for chunk in response:
            text = chunk.choices[0].delta.content if  chunk.choices[0].delta.content else ''
            full_response += text
            yield text
        self.messages.append({"role": "assistant", "content": full_response})

    def one_chat(self, message: Union[str, List[Union[str, Any]]], is_stream: bool = False) -> Union[str, Iterator[str]]:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=message if isinstance(message, list) else [{"role": "user", "content": message}],
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            top_p=self.top_p,
            frequency_penalty=self.frequency_penalty,
            presence_penalty=self.presence_penalty,
            stop=self.stop,
            stream=is_stream
        )
        self._update_stats(response)
        if is_stream:
            return self._handle_streaming_response(response)
        else:
            return response['choices'][0]['text']

    def text_chat(self, message: str, is_stream: bool = False) -> Union[str, Iterator[str]]:
        self.messages.append({"role": "user", "content": message})
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            top_p=self.top_p,
            frequency_penalty=self.frequency_penalty,
            presence_penalty=self.presence_penalty,
            stop=self.stop,
            stream=is_stream
        )
        self._update_stats(response)
        if is_stream:
            return self._handle_streaming_response(response)
        else:
            text_response = response['choices'][0]['text']
            self.messages.append({"role": "assistant", "content": text_response})
            return text_response

    def tool_chat(self, user_message: str, tools: List[Dict[str, Any]], function_module: Any, is_stream: bool = False) -> Union[str, Iterator[str]]:
        iterator = ContinuousStreamIterator(self, user_message, tools, function_module, self.max_tokens, is_stream)
        
        if is_stream:
            return (chunk for chunk in iterator if chunk is not None)
        else:
            return "".join(chunk for chunk in iterator if chunk is not None)

    def _send_tool_request(self, messages, tools):
        return self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    functions=tools,
                    function_call="auto",
                    temperature=self.temperature,
                    top_p=self.top_p,
                    frequency_penalty=self.frequency_penalty,
                    presence_penalty=self.presence_penalty,
                    stop=self.stop,
                )

    def set_task(self, task: str, model: Optional[str] = None) -> None:
        if task == "代码":
            self.model = "deepseek-coder"
            self.temperature = 0.0
        elif task == "数据分析":
            self.model = "deepseek-chat"
            self.temperature = 0.7
        elif task == "对话":
            self.model = "deepseek-chat"
            self.temperature = 1.0
        elif task == "翻译":
            self.model = "deepseek-chat"
            self.temperature = 1.1
        elif task == "创意":
            self.model = "deepseek-chat"
            self.temperature = 1.25
        else:
            raise ValueError("不支持的任务类型")

        if model is not None:
            self.model = model
        self.task = task
        self.messages = []

    def _update_stats(self, response):
        if hasattr(response, 'usage'):
            self.stats["total_tokens"] += response.usage.total_tokens
            self.stats["completion_tokens"] += response.usage.completion_tokens
            self.stats["prompt_tokens"] += response.usage.prompt_tokens
            self.stats["total_cost"] += response.usage.total_tokens * 0.002 / 1000
        self.stats["num_chats"] += 1

    def get_stats(self) -> Dict[str, Any]:
        return self.stats

    def clear_chat(self) -> None:
        self.messages = []

    def image_chat(self, message: str, image_path: str) -> str:
        raise NotImplementedError("DeepSeek API does not support image chat.")

    def audio_chat(self, message: str, audio_path: str) -> str:
        raise NotImplementedError("DeepSeek API does not support audio chat.")

    def video_chat(self, message: str, video_path: str) -> str:
        raise NotImplementedError("DeepSeek API does not support video chat.")
    

class ContinuousStreamIterator:
    def __init__(self, client, initial_message, tools, function_module, max_tokens, temperature, top_p, frequency_penalty,
                 presence_penalty, stop, is_stream):
        self.client = client
        self.history = [{"role": "user", "content": initial_message}]
        self.tools = tools
        self.function_module = function_module
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty
        self.stop = stop
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
            self.current_response = self.client.client.chat.completions.create(
                model=self.client.model,
                max_tokens=self.max_tokens,
                messages=self.history,
                tools=self.tools,
                temperature=self.temperature,
                top_p=self.top_p,
                frequency_penalty=self.frequency_penalty,
                presence_penalty=self.presence_penalty,
                stop=self.stop,
                stream=self.is_stream
            )
        
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
        self.history.append({"role": "assistant", "content": self.assistant_message})
        if self.tool_uses:
            self.state = 'tool_calls'
        else:
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
                function_name = "unknown"
                function_args = {}

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
            self.history.append({"role": "user", "content": tool_result_message})
            self.buffer.append(tool_result_message)
        else:
            self.state = 'final_response'

    def _handle_final_response(self):
        if not self.current_response:
            self.current_response = self.client.client.chat.completions.create(
                model=self.client.model,
                max_tokens=self.max_tokens,
                messages=self.history,
                temperature=self.temperature,
                top_p=self.top_p,
                frequency_penalty=self.frequency_penalty,
                presence_penalty=self.presence_penalty,
                stop=self.stop,
                stream=self.is_stream
            )
        
        if self.is_stream:
            try:
                event = next(self.current_response)
                self._process_event(event)
            except StopIteration:
                self.state = 'finished'
        else:
            content = "".join([c.text for c in self.current_response.content if c.type == 'text'])
            self.buffer.append(content)
            self.state = 'finished'

    def _process_event(self, event):
        for choice in event.choices:
            delta = choice.delta
            if delta.content:
                self.assistant_message += delta.content
                self.buffer.append(delta.content)
            if delta.function_call:
                self.tool_uses.append(delta.function_call)
            elif choice.finish_reason == 'stop':
                if not self.initial_response_complete:
                    self._finalize_initial_response()