from abc import ABC, abstractmethod
from typing import List, Dict, Any


class Ranker(ABC):
    def rank(self, query: str, documents: List[str]) -> List[float]:
        """
        Rank a list of documents based on a query.

        Args:
            query (str): The query to rank the documents against.
            documents (List[str]): A list of documents to rank.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, where each dictionary contains the document and its score.
        """
        pairs = [[query, doc] for doc in documents]
        return self.get_scores(pairs)

    @abstractmethod
    def get_scores(self,pairs:List[List[str]])->List[float]:
        pass