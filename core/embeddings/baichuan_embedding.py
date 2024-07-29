import requests
import json
from ._embedding import Embedding
from ..utils.config_setting import Config

class BaiChuanEmbedding(Embedding):
    def __init__(self,api_key :str = ""):
        config = Config()
        if api_key == "" and config.has_key("baichuan_api_key"):
            api_key = config.get("baichuan_api_key")
        self.api_key = api_key  
        self.url = "http://api.baichuan-ai.com/v1/embeddings"
        self.total_strings = 0
        self.total_tokens = 0
        self.total_successful_requests = 0
        self.total_failed_requests = 0
    """
    返回值：
    [{'index': 0, 'embedding': [0.02789335, 0.032203417,...]
    """
    def convert_to_embedding(self, input_strings):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        data = {
            "model": "Baichuan-Text-Embedding",
            "input": input_strings
        }

        response = requests.post(self.url, headers=headers, data=json.dumps(data))
        result = response.json()

        self.total_strings += len(input_strings)
        self.total_tokens += result["usage"]["total_tokens"]
        successful_requests = len(result["data"])
        failed_requests = len(input_strings) - successful_requests
        self.total_successful_requests += successful_requests
        self.total_failed_requests += failed_requests

        #return result["data"]
        return [item["embedding"] for item in result["data"]]
    
    @property
    def vector_size(self) -> int:
        return 1024

    def get_stats(self):
        return {
            "total_strings": self.total_strings,
            "total_tokens": self.total_tokens,
            "total_successful_requests": self.total_successful_requests,
            "total_failed_requests": self.total_failed_requests
        }

    def print_stats(self):
        stats = self.get_stats()
        print(f"Total strings processed: {stats['total_strings']}")
        print(f"Total tokens used: {stats['total_tokens']}")
        print(f"Total successful requests: {stats['total_successful_requests']}")
        print(f"Total failed requests: {stats['total_failed_requests']}")