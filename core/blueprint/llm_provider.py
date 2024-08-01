
from ..interpreter.ast_code_runner import ASTCodeRunner
from ..embeddings._embedding import Embedding
from ..llms._llm_api_client import LLMApiClient
from ..embeddings.embedding_factory import EmbeddingFactory
from ..llms_cheap.llms_cheap_factory import LLMCheapFactory
from ..llms.llm_factory import LLMFactory
from ..interpreter.data_summarizer import DataSummarizer

class LLMProvider:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMProvider, cls).__new__(cls)
            cls._instance._initialized = False
            cls._instance.__init__()
            
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._llm_factory = LLMFactory()
        self._cheap_factory = LLMCheapFactory()
        self._embedding_factory = EmbeddingFactory()
        self._data_summarizer = DataSummarizer()
        self._llm_client = None
        self._cheap_client = None
        self._embedding_client = None
        self._initialized = True
    
    @property
    def embedding_factory(self):
        return self._embedding_factory

    @property
    def embedding_client(self):
        if self._embedding_client is None:
            self._embedding_client = self._embedding_factory.get_instance()
        return self._embedding_client

    @property
    def llm_factory(self):
        return self._llm_factory
    
    @property
    def cheap_factory(self):
        return self._cheap_factory
    
    @property
    def llm_client(self):
        if self._llm_client is None:
            self._llm_client = self._llm_factory.get_instance()
        return self._llm_client
    
    @property
    def cheap_client(self):
        if self._cheap_client is None:
            self._cheap_client = self._cheap_factory.get_instance()
        return self._cheap_client
    
    def new_llm_client(self)->LLMApiClient:
        return self._llm_factory.get_instance()
    
    def new_cheap_client(self)->LLMApiClient:
        return self._cheap_factory.get_instance()
    
    def new_embedding_client(self)->Embedding:
        return self._embedding_factory.get_instance()
    
    def new_code_runner(self):
        return ASTCodeRunner()