from ..llms.ernie_client import ErnieApiClient


class cheap_ernie(ErnieApiClient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api_name = "ernie-speed-128k" #ernie-3.5-128k
        self.base_url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/{self.api_name}"