
from ..llms.simple_azure import SimpleAzureClient


class CheapAzure(SimpleAzureClient):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.deployment_name = "gpt-4o-mini"