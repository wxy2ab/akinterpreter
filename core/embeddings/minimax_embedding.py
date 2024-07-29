import requests
import json
from typing import List
from ._embedding import Embedding
from ..utils.config_setting import Config

class MiniMaxEmbedding(Embedding):
    def __init__(self):
        config = Config()
        self.api_key = config.get("minimax_api_key")
        #self.group_id = config.get("minimax_group_id")
        self.model = "embo-01"
        self.base_url = "https://api.minimax.chat/v1/embeddings"

    def convert_to_embedding(self, input_strings: List[str], embed_type:str = "db") -> List[List[float]]:
        """
        Convert input strings to embeddings using MiniMax API.

        Args:
            input_strings (List[str]): A list of strings to be converted to embeddings.

        Returns:
            List[List[float]]: A list of embeddings, where each embedding is a list of floats.
        """
        url = f"{self.base_url}"#?GroupId={self.group_id}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "texts": input_strings,
            "model": self.model,
            "type": embed_type  # Using 'db' type as default, can be changed to 'query' if needed
        }

        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            response.raise_for_status()  # Raises an HTTPError for bad responses
            result = response.json()
            return result.get('vectors', [])
        except requests.exceptions.RequestException as e:
            print(f"Error occurred while fetching embeddings: {e}")
            return []

    def get_embedding(self, text: str, emb_type: str = 'db') -> List[float]:
        """
        Get embedding for a single text string.

        Args:
            text (str): The input text to be converted to an embedding.
            emb_type (str): The type of embedding ('db' or 'query'). Defaults to 'db'.

        Returns:
            List[float]: The embedding as a list of floats.
        """
        url = f"{self.base_url}"#?GroupId={self.group_id}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "texts": [text],
            "model": self.model,
            "type": emb_type
        }

        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            response.raise_for_status()
            result = response.json()
            return result.get('vectors', [[]])[0]
        except requests.exceptions.RequestException as e:
            print(f"Error occurred while fetching embedding: {e}")
            return []

    @property
    def vector_size(self) -> int:
        return 1536