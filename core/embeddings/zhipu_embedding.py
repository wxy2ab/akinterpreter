from typing import Any, Dict, List
from abc import ABC, abstractmethod
from ..utils.config_setting import Config
from ._embedding import Embedding

class ZhipuAIEmbeddings(Embedding):
    """ZhipuAI embedding models.

    To use, you should have the ``zhipuai`` python package installed, and the
    environment variable ``ZHIPU_API_KEY`` set with your API key or pass it
    as a named parameter to the constructor.

    More instructions about ZhipuAi Embeddings, you can get it
    from  https://open.bigmodel.cn/dev/api#vector

    Example:
        .. code-block:: python

            embeddings = ZhipuAIEmbeddings(api_key="your-api-key")
            text = "This is a test query."
            query_result = embeddings.convert_to_embedding([text])
            # texts = ["This is a test query1.", "This is a test query2."]
            # query_result = embeddings.convert_to_embedding(texts)
    """

    def __init__(self, model: str = "embedding-2", api_key: str = ""):
        self.model = model
        self.api_key = api_key
        config = Config()
        if self.api_key == "" and config.has_key("glm_api_key"):
            self.api_key = config.get("glm_api_key")
        self._initialize_client()

    def _initialize_client(self):
        try:
            from zhipuai import ZhipuAI
            self.client = ZhipuAI(api_key=self.api_key)
        except ImportError:
            raise ImportError(
                "Could not import zhipuai python package."
                "Please install it with `pip install zhipuai`."
            )

    def convert_to_embedding(self, input_strings: List[str]) -> List[List[float]]:
        """
        Convert input strings to embeddings.

        Args:
            input_strings (List[str]): A list of strings to be converted to embeddings.

        Returns:
            List[List[float]]: A list of embeddings, where each embedding is a list of floats.
        """
        resp = self.client.embeddings.create(model=self.model, input=input_strings)
        embeddings = [r.embedding for r in resp.data]
        return embeddings