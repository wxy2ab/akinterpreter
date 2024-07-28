
from ._step_abstract import StepInfoGenerator


class DataAnalysisStepInfoGenerator(StepInfoGenerator):
    @property
    def step_description(self) -> str:
        return "Data Analysis Step"

    def gen_step_info(self, step_data_type, query):
        pass

    def validate_step_info(self, step_data):
        pass

    def fix_step_info(self, step_data, query, error_msg):
        pass