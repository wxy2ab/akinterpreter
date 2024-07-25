from ..llms.gemini_client import GeminiAPIClient
from vertexai.preview.generative_models import GenerativeModel

class CheapGemini(GeminiAPIClient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = GenerativeModel("gemini-1.5-flash-001")
        self.chat = self.model.start_chat()