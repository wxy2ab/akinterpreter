

from .tushare_data_retrieval_step_info_generator import TushareDataRetrievalStepInfoGenerator
from .step_info_generator_collection import StepInfoGeneratorCollection
from .akshare_data_retrieval_step_info_generator import AkShareDataRetrievalStepInfoGenerator
from .data_analysis_step_info_generator import DataAnalysisStepInfoGenerator


class CurrentGeneratorCollection(StepInfoGeneratorCollection):
    def __init__(self):
        super().__init__()
        self.add(AkShareDataRetrievalStepInfoGenerator())
        self.add(DataAnalysisStepInfoGenerator())
        from ..utils.config_setting import Config
        config = Config()
        if config.has_key("tushare_key"):
            tushare_key = config.get("tushare_key")
            self.add(TushareDataRetrievalStepInfoGenerator(tushare_key))
        