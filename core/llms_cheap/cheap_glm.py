from ..llms.glm_client import GLMClient

class CheapGLM(GLMClient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = "GLM-4-Air" #GLM-4-Flash