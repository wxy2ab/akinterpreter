from .moonshot_client import MoonShotClient
from ..utils.config_setting import Config
from ._llm_api_client import LLMApiClient


# curl https://api.qnaigc.com/api/llmapikey -H "Authorization: <你的 AK>"
# # 输出
# {"api_key":"sk-xxxxx","old_key":"sk-xxxxx","status":true}% 

#https://eastern-squash-d44.notion.site/DeepSeek-R1-V3-Qwen2-API-1932c3f43aee803c8d7ce5ba8cb195b1

class QiniuDeepSeekClient(LLMApiClient):
    pass


class QiniuDeepSeekClient(MoonShotClient):
    def __init__(self, model: str = "deepseek-v3-0324"):
        base_url = "https://api.qnaigc.com/v1/"

        config = Config()

        api_key = config.get("qiniu_api_key")
        super().__init__(api_key, base_url, max_tokens=8192)
        if model is None or model == "":
            model = "deepseek-v3-0324"
        self.model = model

