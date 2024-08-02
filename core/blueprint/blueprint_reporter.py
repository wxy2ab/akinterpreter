from typing import Generator
from ..planner.message import send_message
from .step_model_collection import StepModelCollection
from .llm_provider import LLMProvider
from .step_data import StepData

class BluePrintReporter:
    def __init__(self, step_info: StepModelCollection, step_data: StepData):
        self.step_data = step_data
        self.step_info = step_info
        self.llm_provider = LLMProvider()
        self.llm_client = self.llm_provider.new_llm_client()
        self._report = ""
    
    @property
    def report(self) -> str:
        return self._report

    def report(self) -> Generator[str, None, None]:
        query = self.step_info.query_summary
        analysis_results = []
        for step in self.step_info:
            if hasattr(step,'analysis_result'):
                step_result = step.analysis_result
                result = self.step_data[step_result]
                analysis_results.append({
                    "task": step.description,
                    "result": result
                })
        if len(analysis_results) == 0:
            yield send_message("没有可供报告的结果。", "error")
            raise Exception("没有可供报告的结果。")
        
        prompt = self.create_report_prompt(query, analysis_results)
        
        # Generate the report using the LLM with streaming
        report_stream = self.llm_client.one_chat(prompt, is_stream=True)
        
        # Process the streamed response
        full_report = ""
        for chunk in report_stream:
            full_report += chunk
            yield send_message(chunk,"report")  # Yield each chunk as it's received
        
        # Assign the complete report to self._report
        self._report = full_report
        self.step_data.report = full_report
        yield send_message("报告已生成。", "report")

    @staticmethod
    def create_report_prompt(initial_query: str, results_summary: list) -> str:
        formatted_results = "\n".join([f"任务: {result['task']}\n结果: {result['result']}\n" for result in results_summary])
        
        return f"""
        基于以下初始查询和分析结果，生成一份全面的报告,以Markdown格式提供：

        查询：
        {initial_query}

        分析结果：
        {formatted_results}

        请生成一份全面的报告，总结数据分析的发现和洞察。报告应该：
        1. 回答初始查询
        2. 总结每个分析任务的主要发现
        3. 提供整体的见解和结论
        4. 指出任何有趣或意外的发现
        5. 如果适用，提供进一步分析的建议

        报告应结构清晰、表述明确，并提供有意义的结论。
        """