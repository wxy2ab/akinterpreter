import requests
from typing import List
from ._embedding import Embedding
from ..utils.config_setting import Config

class VolcengineEmbedding(Embedding):
    def __init__(self):
        config = Config()
        self.api_key = config.get("volcengine_api_key")
        self.model = config.get("volcengine_embedding")
        self.url = "https://ark.cn-beijing.volces.com/api/v3/embeddings"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        self.stats = {
            "total_strings": 0,
            "total_tokens": 0,
            "total_successful_requests": 0,
            "total_failed_requests": 0
        }

    def convert_to_embedding(self, input_strings: List[str]) -> List[List[float]]:
        payload = {
            "model": self.model,
            "input": input_strings
        }

        try:
            response = requests.post(self.url, headers=self.headers, json=payload)
            response.raise_for_status()
            result = response.json()

            self.stats["total_strings"] += len(input_strings)
            self.stats["total_tokens"] += result["usage"]["total_tokens"]
            self.stats["total_successful_requests"] += 1

            return [item["embedding"] for item in result["data"]]

        except requests.RequestException as e:
            self.stats["total_failed_requests"] += 1
            print(f"Error occurred while making the request: {str(e)}")
            return []

    def get_stats(self):
        return self.stats

    def print_stats(self):
        print(f"Total strings processed: {self.stats['total_strings']}")
        print(f"Total tokens used: {self.stats['total_tokens']}")
        print(f"Total successful requests: {self.stats['total_successful_requests']}")
        print(f"Total failed requests: {self.stats['total_failed_requests']}")

    @property
    def vector_size(self) -> int:
        return 2560