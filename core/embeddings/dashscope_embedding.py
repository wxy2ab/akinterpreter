from __future__ import annotations

import logging
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
)
from abc import ABC, abstractmethod

from requests.exceptions import HTTPError
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from ._embedding import Embedding
from ..utils.log import logger
from ..utils.config_setting import Config


def _create_retry_decorator(embeddings: DashScopeEmbeddings) -> Callable[[Any], Any]:
    multiplier = 1
    min_seconds = 1
    max_seconds = 4
    # Wait 2^x * 1 second between each retry starting with
    # 1 seconds, then up to 4 seconds, then 4 seconds afterwards
    return retry(
        reraise=True,
        stop=stop_after_attempt(embeddings.max_retries),
        wait=wait_exponential(multiplier, min=min_seconds, max=max_seconds),
        retry=(retry_if_exception_type(HTTPError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )


def embed_with_retry(embeddings: DashScopeEmbeddings, **kwargs: Any) -> Any:
    """Use tenacity to retry the embedding call."""
    retry_decorator = _create_retry_decorator(embeddings)

    @retry_decorator
    def _embed_with_retry(**kwargs: Any) -> Any:
        result = []
        i = 0
        input_data = kwargs["input"]
        while i < len(input_data):
            kwargs["input"] = input_data[i : i + 25]
            resp = embeddings.client.call(**kwargs)
            if resp.status_code == 200:
                result += resp.output["embeddings"]
            elif resp.status_code in [400, 401]:
                raise ValueError(
                    f"status_code: {resp.status_code} \n "
                    f"code: {resp.code} \n message: {resp.message}"
                )
            else:
                raise HTTPError(
                    f"HTTP error occurred: status_code: {resp.status_code} \n "
                    f"code: {resp.code} \n message: {resp.message}",
                    response=resp,
                )
            i += 25
        return result

    return _embed_with_retry(**kwargs)


class DashScopeEmbeddings(Embedding):
    """DashScope embedding models.

    To use, you should have the ``dashscope`` python package installed, and the
    environment variable ``DASHSCOPE_API_KEY`` set with your API key or pass it
    as a named parameter to the constructor.

    Example:
        .. code-block:: python

            embeddings = DashScopeEmbeddings(dashscope_api_key="my-api-key")

    Example:
        .. code-block:: python

            import os
            os.environ["DASHSCOPE_API_KEY"] = "your DashScope API KEY"

            embeddings = DashScopeEmbeddings(
                model="text-embedding-v1",
            )
            text = "This is a test query."
            query_result = embeddings.embed_query(text)

    """

    def __init__(self, model: str = "text-embedding-v1", dashscope_api_key: Optional[str] = None, max_retries: int = 5):
        import dashscope
        config=Config()
        if dashscope_api_key is None and config.has_key("DASHSCOPE_API_KEY"):
            dashscope_api_key = config.get("DASHSCOPE_API_KEY")
        self.model = model
        self.dashscope_api_key = dashscope_api_key or self._get_api_key_from_env()
        self.max_retries = max_retries
        dashscope.api_key = self.dashscope_api_key
        self.client = dashscope.TextEmbedding

    def _get_api_key_from_env(self) -> str:
        import os
        return os.getenv("DASHSCOPE_API_KEY", "")

    def convert_to_embedding(self, input_strings: List[str]) -> List[List[float]]:
        """Convert input strings to embeddings."""
        embeddings = embed_with_retry(
            self, input=input_strings, text_type="document", model=self.model
        )
        embedding_list = [item["embedding"] for item in embeddings]
        return embedding_list

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Call out to DashScope's embedding endpoint for embedding search docs.

        Args:
            texts: The list of texts to embed.
            chunk_size: The chunk size of embeddings. If None, will use the chunk size
                specified by the class.

        Returns:
            List of embeddings, one for each text.
        """
        return self.convert_to_embedding(texts)

    def embed_query(self, text: str) -> List[float]:
        """Call out to DashScope's embedding endpoint for embedding query text.

        Args:
            text: The text to embed.

        Returns:
            Embedding for the text.
        """
        embedding = embed_with_retry(
            self, input=text, text_type="query", model=self.model
        )[0]["embedding"]
        return embedding