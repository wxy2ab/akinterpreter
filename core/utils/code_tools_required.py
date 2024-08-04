from core.blueprint.llm_provider import LLMProvider
from .single_ton import Singleton

from .config_setting import Config

class CodeToolsRequired(metaclass=Singleton):
    def __init__(self):
        self.required = False
        from .code_tools import code_tools
        self._tools = code_tools
        config = Config()
        self.llm_provider = LLMProvider()
        
        self.default_vars = {
            "llm_provider": self.llm_provider,
            "llm_client": self.llm_provider.new_llm_client(),
            "llm_factory": self.llm_provider.llm_factory,
            "data_summarizer": self.llm_provider._data_summarizer,
            "code_runner":self.llm_provider.new_code_runner()
        }
        if config.has_key("tushare_key"):
            tushare_key = config.get("tushare_key")
            import tushare as ts
            ts.set_token(tushare_key)
            self.default_vars["ts"] = ts
            from ..tushare_doc.ts_code_matcher import TsCodeMatcher
            tsgetter = TsCodeMatcher()
            self.default_vars["tsgetter"] = tsgetter
        self.add_required()

    def add_required(self):
        default_vars = self.default_vars
        for name, value in default_vars.items():
            if not self._tools.is_exists(name):
                self._tools.add_var(name, value)

    def is_required(self):
        return self.required
    



add_required_tools = CodeToolsRequired()
