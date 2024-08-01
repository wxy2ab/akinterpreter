

from core.blueprint.step_data import StepData


class BluePrintReporter:
    def __init__(self,step_data:StepData):
        self.step_data = step_data
    
    def report(self):
        pass