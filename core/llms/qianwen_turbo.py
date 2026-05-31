from .moonshot_client import MoonShotClient
from ..utils.config_setting import Config
from ._llm_api_client import LLMApiClient
import traceback

class QianWenTurboClient(LLMApiClient):
    pass

class QianWenTurboClient(MoonShotClient):
    def __init__(self, model: str = "qwen3-8b"):
        base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        config = Config()
        api_key = config.get("dashscope_api_key")
        super().__init__(api_key, base_url, max_tokens=8192)
        if model is None or model == "":
            model = "qwen3-8b"
        self.model = model

        # 输出完整的调用堆栈
        print("=" * 80)
        print("调用堆栈跟踪:")
        print("=" * 80)
        traceback.print_stack()
        print("=" * 80)
        
        raise DeprecationWarning("QianWenTurboClient is deprecated, please use QianWenClient instead")