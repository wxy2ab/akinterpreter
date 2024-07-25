import requests
import json
from typing import List, Tuple
from abc import ABC, abstractmethod
from ..utils.config_setting import Config
from ._ranker import Ranker

class BaiduBCEReranker(Ranker):
    def __init__(self, api_key: str = "", secret_key: str = "", model_name: str = "bce_reranker_base"):
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
        self.reranker_url = f"{self.base_url}/rpc/2.0/ai_custom/v1/wenxinworkshop/reranker/{self.model_name}"

    def get_access_token(self):
        url = f"{self.base_url}/oauth/2.0/token?grant_type=client_credentials&client_id={self.api_key}&client_secret={self.secret_key}"
        response = requests.post(url)
        data = response.json()
        self.access_token = data.get("access_token")
        return self.access_token

    def rerank(self, query: str, documents: List[str]) -> List[float]:
        if not self.access_token:
            self.get_access_token()

        headers = {
            "Content-Type": "application/json"
        }

        payload = {
            "query": query,
            "documents": documents
        }

        params = {
            "access_token": self.access_token
        }

        try:
            response = requests.post(self.reranker_url, headers=headers, params=params, json=payload)
            response.raise_for_status()
            result = response.json()
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            print(f"Response content: {response.text if response else 'No response'}")
            raise

        if "error_code" in result:
            print(f"API returned an error: {result}")
            raise Exception(f"重排序失败：{result.get('error_msg', 'Unknown error')}")

        # Sort the results by index to ensure the order matches the input documents
        sorted_results = sorted(result.get("results", []), key=lambda x: x["index"])
        
        # Extract and return the relevance scores
        return [item["relevance_score"] for item in sorted_results]

    def get_scores(self, documents: List[Tuple[str, str]]) -> List[float]:
        from collections import defaultdict
        # Group documents by query
        query_docs = defaultdict(list)
        for query, doc in documents:
            query_docs[query].append(doc)

        all_scores = []

        for query, docs in query_docs.items():
            scores = self.rerank(query, docs)
            all_scores.extend(scores)

        return all_scores