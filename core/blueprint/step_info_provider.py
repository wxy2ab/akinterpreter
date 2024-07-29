from .current_generator_collection import CurrentGeneratorCollection



class StepInfoProvider:
    def __init__(self):
        self.generators = CurrentGeneratorCollection()
    
    def get_build_prompt(self, query: str) -> str:
        pass
