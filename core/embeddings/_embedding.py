from abc import ABC, abstractmethod
from typing import List, Dict, Any

class Embedding(ABC):

    @abstractmethod
    def convert_to_embedding(self, input_strings: List[str]) -> List[List[float]]:
        """
        Convert input strings to embeddings.

        Args:
            input_strings (List[str]): A list of strings to be converted to embeddings.

        Returns:
            List[List[float]]: A list of embeddings, where each embedding is a list of floats.
        """
        pass
    
    @property
    @abstractmethod
    def vector_size(self) -> int:
        """
        Get the size of the embeddings.

        Returns:
            int: The size of the embeddings.
        """
        pass
