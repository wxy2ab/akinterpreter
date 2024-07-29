
from ..llms_cheap.llms_cheap_factory import LLMCheapFactory
from ..llms.llm_factory import LLMFactory


class LLMProvider:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMProvider, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._llm_factory = LLMFactory()
        self._cheap_factory = LLMCheapFactory()
        self._llm_client = None
        self._cheap_client = None
        self._initialized = True
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
    def new_llm_client(self):
        return self._llm_factory.get_instance()
    def new_cheap_client(self):
        return self._cheap_factory.get_instance()