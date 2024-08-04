from core.planner.message import send_message
from ..rag.memeory import Memory
from ._step_abstract import StepInfoGenerator,StepCodeGenerator,StepExecutor
from .llm_provider import LLMProvider
from .tushare_data_retrieval_step_model import TushareDataRetrievalStepModel
from typing import Any, Dict, Generator, Type
from ._base_step_model import BaseStepModel
from .tushare_data_retrieval_step_code_generator import TushareDataRetrievalStepCodeGenerator
from .data_retrieval_step_executor import DataRetrievalStepExecutor



class TushareDataRetrievalStepInfoGenerator(StepInfoGenerator):
    def __init__(self,tushare_key:str) -> None:
        if not tushare_key:
            raise ValueError("tushare_key is required")
        self.retrieval = Memory.load_from_file("./json/tushare_memory.json")
        self.llm_provider = LLMProvider()
        self.llm_client = self.llm_provider.new_llm_client()
        self.llm_cheap_client  = self.llm_provider.new_cheap_client()
        import tushare  as ts
        ts.set_token(tushare_key)
        from ..utils.code_tools import code_tools
        code_tools.add_with_recover("ts",ts)
        from ..tushare_doc.ts_code_matcher import TsCodeMatcher
        tsgetter = TsCodeMatcher()
        code_tools.add_with_recover("tsgetter",tsgetter)

    
    @property
    def step_description(self) -> str:
        return "提供沪深股票，指数，公募基金，期货，现货，期权，债券，外汇，港股，美股，电影票房，剧本备案，利率，GDP，CPI，PPI，PMI，新闻、上市公司公告等方面的数据,数据质量高，请优先使用"
    
    @property
    def step_model(self) -> Type[BaseStepModel]:
        return TushareDataRetrievalStepModel
    
    @property
    def step_code_generator(self) -> Type["StepCodeGenerator"]:
        return TushareDataRetrievalStepCodeGenerator
    
    @property
    def step_executor(self) -> Type["StepExecutor"]:
        return DataRetrievalStepExecutor

    def get_step_model(self) -> BaseStepModel:
        return TushareDataRetrievalStepModel()

    def gen_step_info(self, step_info:dict, query:str)-> Generator[Dict[str, Any], None, TushareDataRetrievalStepModel]:
        step = TushareDataRetrievalStepModel()
        step.description = step_info["task"]
        step.save_data_to=step_info["save_data_to"]
        step.required_data=step_info["required_data"]
        yield send_message(type="plan",content="获取可用函数\n")
        selected_functions = self.retrieval.get_functions(query)
        step.selected_functions = selected_functions
        yield send_message(type="plan",content="完成步骤\n")
        yield send_message(type="plan",content="data: [Done]",data=step)
        return step

    def validate_step_info(self, step_info: dict) -> tuple[str, bool]:
        task = step_info.get("task", "")
        documents = self.retrieval.search_documents(task, topk=50)
        
        # 构建简洁的提示词
        function_descriptions = "\n".join([doc for doc in documents])
        prompt = f"""
        任务: {task}

        可用的函数库描述:
        {function_descriptions}
        
        仅回答：如果任务可以使用给定函数库完成，回复"可以完成"；如果无法完成，回复"无法完成"并简要说明原因。

        注意：
        - 除非确定查询所需的日期不可完成，否则不要因为日期问题而回复无法完成
        - 函数描述中除非专门描述了限制，否则不应该假设其存在限制，比如news接口，不应该假设其只能获取最近一天的新闻

        回复:
        """
        
        result = self.llm_cheap_client.one_chat(prompt)
        
        if result.strip().startswith("无法完成"):
            # 提取原因（去掉"无法完成"前缀）
            reason = result.strip()[4:].strip()
            return reason, False
        elif result.startswith("可以完成"):
            return "", True
        else:
            # 处理意外的回复
            return "无法确定是否可以完成任务", False

    def fix_step_info(self, step_data, query, error_msg) -> Generator[Dict[str, Any], None, None]:
        pass

    def gen_new_description(self, step_data) -> Generator[Dict[str, Any], None, str]:
        # 获取初始任务描述
        description = step_data.get("task", "")
        save_data_to = step_data.get("save_data_to", "")
        required_data = step_data.get("required_data", [])

        # 准备提示词
        prompt = f"任务: {description}\n需要的变量: {required_data}\n将数据保存到: {save_data_to}\n请优化这段任务描述，使其更清晰并更有助于代码生成。"

        # 使用llm_client生成优化后的描述
        optimized_description = yield from self.llm_client.one_chat(prompt, is_stream=True)

        return optimized_description