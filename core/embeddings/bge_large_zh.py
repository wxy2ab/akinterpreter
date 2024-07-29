import requests
import json
from typing import List, Dict, Any
from abc import ABC, abstractmethod
from ..utils.config_setting import Config
from ._embedding import Embedding

class BGELargeZhAPI(Embedding):
    def __init__(self, api_key: str = "", secret_key: str = "",model_name: str = "bge_large_zh"):
        config = Config()
        if api_key == "" and config.has_key("ERNIE_API_KEY"):
            api_key = config.get("ERNIE_API_KEY")
        if secret_key == "" and config.has_key("ERNIE_SERCRET_KEY"):
            secret_key = config.get("ERNIE_SERCRET_KEY")
        self.api_key = api_key
        self.secret_key = secret_key
        self.model_name = model_name
        self.access_token = None
        self.base_url = "https://aip.baidubce.com"
        self.embeddings_url = f"{self.base_url}/rpc/2.0/ai_custom/v1/wenxinworkshop/embeddings/{self.model_name}"

    def get_access_token(self):  
        url = "https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=" + self.api_key + "&client_secret=" + self.secret_key  
        response = requests.post(url)  
        data = response.json()  
        self.access_token = data.get("access_token")  
        return self.access_token  

    def generate_embeddings(self, texts: List[str], user_id: str = None) -> Dict[str, Any]:
        """
        生成文本的embedding
        :param texts: 输入文本列表
        :param user_id: 可选，用户ID
        :return: 包含embedding结果的字典
        """
        if not self.access_token:
            self.get_access_token()

        headers = {
            "Content-Type": "application/json"
        }

        payload = {
            "input": texts
        }
        if user_id:
            payload["user_id"] = user_id

        params = {
            "access_token": self.access_token
        }

        # print(f"Sending request to {self.embeddings_url}")
        # print(f"Headers: {headers}")
        # print(f"Params: {params}")
        # print(f"Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")

        try:
            response = requests.post(self.embeddings_url, headers=headers, params=params, json=payload)
            response.raise_for_status()  # 如果响应状态码不是 2xx，这将引发一个异常
            result = response.json()
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            print(f"Response content: {response.text if response else 'No response'}")
            raise

        if "error_code" in result:
            print(f"API returned an error: {result}")
            raise Exception(f"生成embedding失败：{result.get('error_msg', 'Unknown error')}")

        return result

    def convert_to_embedding(self, input_strings: List[str]) -> List[List[float]]:
        result = self.generate_embeddings(input_strings)
        return [embedding["embedding"] for embedding in result.get("data", [])]
    
    @property
    def vector_size(self) -> int:
        return 1024