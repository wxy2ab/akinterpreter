from ..llms.mini_max_client import MiniMaxClient


class CheapMiniMax(MiniMaxClient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)