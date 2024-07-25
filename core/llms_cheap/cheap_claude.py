
from ..llms.simple_claude import SimpleClaudeAwsClient


class CheapClaude(SimpleClaudeAwsClient):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.model = "anthropic.claude-3-haiku-20240307-v1:0"
        