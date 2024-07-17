
import requests
import json
from typing import Generator, Iterator, List, Dict, Any, Union
from ._llm_api_client import LLMApiClient

from ..utils.log import logger

class BaichuanClient(LLMApiClient):
    def __init__(self,  model: str = "Baichuan4", temperature: float = 0.3, 
                 top_p: float = 0.85, top_k: int = 5, max_tokens: int = 2048):
        from ..utils.config_setting import Config
        config  = Config()
        api_key = config.get("baichuan_api_key")
        self.api_key = api_key
        self.base_url = "https://api.baichuan-ai.com/v1/chat/completions"
        self.model = model
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        self.parameters = {
            "model": self.model,
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "max_tokens": max_tokens,
            "stream": False
        }

    def text_chat(self, message: str, is_stream: bool = False) -> Union[str, Iterator[str]]:
        data = {
            "messages": [{"role": "user", "content": message}],
            "stream": is_stream,
            **self.parameters
        }
        logger.debug(f"Sending request to Baichuan API: {json.dumps(data, indent=2)}")
        try:
            response = requests.post(self.base_url, headers=self.headers, json=data, stream=is_stream)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            raise

        if is_stream:
            return self._process_stream(response)
        else:
            return self._process_response(response)

    def tool_chat(self, user_message: str, tools: List[Dict[str, Any]], function_module: Any, is_stream: bool = False) -> Union[str, Iterator[str]]:
        # First round: Send message with tools
        data = {
            "messages": [{"role": "user", "content": user_message}],
            "stream": False,  # First call is always non-stream
            "tools": tools,
            "tool_choice": "auto",
            **self.parameters
        }
        try:
            response = requests.post(self.base_url, headers=self.headers, json=data)
            response.raise_for_status()
            response_data = response.json()
        except requests.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
        except json.JSONDecodeError:
            raise Exception("Failed to parse API response")

        logger.debug(f"First round response: {response_data}")

        # Check if there are tool calls
        if 'choices' in response_data and response_data['choices']:
            message = response_data['choices'][0].get('message', {})
            if 'tool_calls' in message:
                tool_calls = message['tool_calls']
                function_results = []

                # Execute each tool call
                for tool_call in tool_calls:
                    function_name = tool_call['function']['name']
                    try:
                        arguments = json.loads(tool_call['function']['arguments'])
                    except json.JSONDecodeError:
                        raise ValueError(f"Invalid JSON in function arguments for {function_name}")
                    
                    # Call the function from the provided module
                    if hasattr(function_module, function_name):
                        function = getattr(function_module, function_name)
                        try:
                            result = function(**arguments)
                            function_results.append({
                                "role": "tool",
                                "content": json.dumps(result),
                                "tool_call_id": tool_call['id']
                            })
                        except Exception as e:
                            raise Exception(f"Error calling function {function_name}: {str(e)}")
                    else:
                        raise ValueError(f"Function {function_name} not found in the provided module")

                # Second round: Send function results
                data['messages'].extend(function_results)
                data['stream'] = is_stream  # Use the requested stream setting for second call
                
                try:
                    response = requests.post(self.base_url, headers=self.headers, json=data, stream=is_stream)
                    response.raise_for_status()
                except requests.RequestException as e:
                    raise Exception(f"API request failed in second round: {str(e)}")
                
                if is_stream:
                    return self._process_stream(response)
                else:
                    return self._process_response(response)
            else:
                # If no tool calls, return the assistant's message
                return message.get('content', '')
        else:
            raise Exception("Unexpected response format from API")

    def _process_response(self, response: requests.Response) -> str:
        if response.status_code == 200:
            content = response.json()
            return content['choices'][0]['message']['content']
        else:
            raise Exception(f"API request failed with status code {response.status_code}: {response.text}")

    def _process_stream(self, response: requests.Response) -> Iterator[str]:
        logger.debug("Starting to process stream response")
        for line in response.iter_lines():
            if line:
                try:
                    logger.debug(f"Raw line: {line}")
                    data = json.loads(line)
                    logger.debug(f"Parsed JSON: {data}")

                    if 'choices' in data and data['choices']:
                        choice = data['choices'][0]
                        if 'message' in choice and 'content' in choice['message']:
                            content = choice['message']['content']
                            logger.debug(f"Yielding content: {content}")
                            yield content
                        elif 'delta' in choice and 'content' in choice['delta']:
                            content = choice['delta']['content']
                            logger.debug(f"Yielding content: {content}")
                            yield content
                        if choice.get('finish_reason') == 'stop':
                            logger.debug("Received stop signal")
                            break
                    else:
                        logger.warning(f"Unexpected data format: {data}")

                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {str(e)}")
                except Exception as e:
                    logger.error(f"Error processing stream: {str(e)}", exc_info=True)

        logger.debug("Stream processing completed")

    def audio_chat(self, message: str, audio_path: str) -> str:
        raise NotImplementedError("Baichuan API does not support audio chat.")

    def video_chat(self, message: str, video_path: str) -> str:
        raise NotImplementedError("Baichuan API does not support video chat.")

    def clear_chat(self):
        # Baichuan API doesn't maintain chat history, so this method is a no-op
        pass

    def one_chat(self, message: Union[str, List[Union[str, Any]]], is_stream: bool = False) -> Union[str, Iterator[str]]:
        if isinstance(message, str):
            return self.text_chat(message, is_stream)
        elif isinstance(message, list):
            data = {
                "messages": message,
                "stream": is_stream,
                **self.parameters
            }
            response = requests.post(self.base_url, headers=self.headers, json=data, stream=is_stream)
            
            if is_stream:
                return self._process_stream(response)
            else:
                return self._process_response(response)

    def get_stats(self) -> Dict[str, Any]:
        # Baichuan API doesn't provide usage statistics directly
        # You might want to implement your own tracking mechanism
        return {"message": "Usage statistics not available for Baichuan API"}

    def _process_response(self, response: requests.Response) -> str:
        if response.status_code == 200:
            content = response.json()
            return content['choices'][0]['message']['content']
        else:
            raise Exception(f"API request failed with status code {response.status_code}: {response.text}")

    def set_parameters(self, **kwargs):
        valid_params = ["temperature", "top_p", "top_k", "max_tokens", "stream", "model"]
        for key, value in kwargs.items():
            if key in valid_params:
                self.parameters[key] = value
            else:
                print(f"Warning: {key} is not a valid parameter for Baichuan API and will be ignored.")