from ..llms.doubao_client import DoubaoApiClient

class CheapDoubao(DoubaoApiClient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = "doubao-lite-128k"