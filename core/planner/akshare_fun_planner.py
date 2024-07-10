import asyncio
from datetime import datetime
import os
import re
import traceback

from core.scheduler.schedule_manager import SchedulerManager
from ..akshare_doc.akshare_data_singleton import AKShareDataSingleton
from typing import List, Dict, Tuple, Union,Optional,Any
import json
from typing import Generator, Dict, Any, List, Optional
from ..llms.llm_factory import LLMFactory
from ..llms._llm_api_client import LLMApiClient
from ..interpreter.sse_code_runner import SSECodeRunner
from ..interpreter.data_summarizer import DataSummarizer
from ..interpreter._sse_planner import SSEPlanner, RetrievalProvider
from .akshare_prompts import AksharePrompts
from ..llms.llm_factory import LLMFactory
from .akshare_retrieval_provider import AkshareRetrievalProvider
from .steps_plan_manager import StepsPlanManager
from .parse_query_as_command import create_command_parser

class AkshareFunPlanner(SSEPlanner):
    def __init__(self, max_retry=8, allow_yfinance: bool = False):
        self.llm_factory = LLMFactory()
        self.llm_client = self.llm_factory.get_instance()
        self.code_runner = SSECodeRunner()
        self.data_summarizer = DataSummarizer()
        self.retriever = AkshareRetrievalProvider()
        self.plan_manager = StepsPlanManager(max_retry=max_retry, allow_yfinance=allow_yfinance)
        self.prompts = AksharePrompts()
        self.task_saved_path:str = ""
        self.stop_every_step:bool = False
        self.command_parser = create_command_parser()
    
    def set_max_retry(self, max_retry: int) -> Generator[Dict[str, Any], None, None]:
        self.plan_manager.max_retry = max_retry
        yield {"type": "message", "content": f"最大重试次数已设置为 {max_retry}"}

    def set_allow_yfinance(self, allow_yfinance: bool) -> Generator[Dict[str, Any], None, None]:
        self.plan_manager.allow_yfinance = allow_yfinance
        yield {"type": "message", "content": f"允许使用 yfinance: {allow_yfinance}"}

    def get_allow_yfinance(self) -> bool:
        return self.plan_manager.allow_yfinance

    def get_max_retry(self) -> int:
        return self.plan_manager.max_retry

    def show_step_code(self, step: int) -> Generator[Dict[str, Any], None, None]:
        code = self.plan_manager.get_step_code(step)
        if code:
            yield {"type": "code", "content": f"步骤 {step} 的代码：\n{code}"}
        else:
            yield {"type": "error", "content": f"步骤 {step} 的代码不存在"}

    def modify_step_code(self, step: int, query: str) -> Generator[Dict[str, Any], None, None]:
        yield from self.plan_manager.modify_step_code(step, query)

    def reset(self) -> Generator[Dict[str, Any], None, None]:
        self.task_saved_path = ""
        self.plan_manager.reset()
        yield {"type": "message", "content": "所有数据已重置，可以重新开始。"}
    
    def _parse_special_commands(self, query: str) -> Generator[Dict[str, Any], bool, None]:
        return self.command_parser.parse(query, self)

    def show_all_commands(self):
        commands = self.command_parser.get_help()
        for cmd, help_text in commands:
            print(f"{cmd}: {help_text}")

    def plan_chat(self, query: str) -> Generator[Dict[str, Any], None, None]:
        # 首先尝试解析特殊命令
        command_handled = yield from self._parse_special_commands(query)
        if command_handled:
            return

        # 如果不是特殊命令，则继续原有的计划创建或修改逻辑
        if self.plan_manager.current_plan == {}:
            yield from self.plan_manager.create_plan(query)
        else:
            yield from self.plan_manager.modify_plan(query)

        # 计划创建或修改完成后，提示用户确认
        if self.plan_manager.current_plan:
            yield {"type": "plan", "content": self.plan_manager.current_plan}
            yield {"type": "message", "content": "计划生成完毕。请检查计划并输入'确认计划'来开始执行，或继续修改计划。"}

        # 如果计划已确认，开始执行
        if self.plan_manager.is_plan_confirmed:
            progress_generator = self.stream_progress()
            while True:
                try:
                    progress_info = next(progress_generator)
                    yield progress_info
                    if progress_info['type'] == 'pause':
                        user_input = yield {"type": "input_required"}
                        if user_input.lower() != "continue":
                            command_handled = yield from self._parse_special_commands(user_input)
                            if command_handled:
                                continue
                        else:
                            yield {"type": "message", "content": "继续执行下一步。"}
                            progress_generator = self.stream_progress()
                except StopIteration:
                    break  # 所有步骤已完成

    def handle_confirm_plan(self) -> Generator[Dict[str, Any], None, None]:
        if not self.plan_manager.current_plan:
            yield {"type": "error", "content": "没有可确认的计划。请先创建一个计划。"}
            return

        self.plan_manager.is_plan_confirmed = True
        yield {"type": "message", "content": "计划已确认。开始执行计划。"}
        yield from self.stream_progress()

    def stream_progress(self) -> Generator[Dict[str, Any], None, None]:
        while self.plan_manager.current_step_number < self.plan_manager.total_steps:
            current_step = self.plan_manager.get_current_step()
            total_steps = self.plan_manager.total_steps
            step_number = self.plan_manager.current_step_number + 1

            yield {
                "type": "progress",
                "content": {
                    "step": step_number,
                    "total_steps": total_steps,
                    "description": current_step['description'],
                    "progress": step_number / total_steps
                }
            }

            yield from self.step()

            if self.stop_every_step:
                yield {"type": "pause", "content": "步骤执行完成。等待用户确认继续。"}
                return  # 暂停执行，返回控制权给 plan_chat

        # 所有步骤完成后，生成最终报告
        yield {"type": "message", "content": "所有步骤已完成。正在生成最终报告..."}
        yield from self.get_final_report()

    def step(self) -> Generator[Dict[str, Any], None, None]:
        try:
            yield from self.plan_manager.step()
        except Exception as e:
            yield {"type": "error", "content": f"执行步骤时发生错误: {str(e)}"}
            yield from self.handle_error(e)

    def handle_error(self, error: Exception) -> Generator[Dict[str, Any], None, None]:
        error_message = str(error)
        yield {"type": "error", "content": error_message}
        
        fix_prompt = f"发生了一个错误：{error_message}。请提供解决方案或下一步建议。"
        for chunk in self.llm_client.text_chat(fix_prompt, is_stream=True):
            yield {"type": "solution", "content": chunk}

    def get_final_report(self) -> Generator[Dict[str, Any], None, None]:
        try:
            # 调用 StepsPlanManager 的 get_final_report 方法
            report_generator = self.plan_manager.get_final_report()
            report_data = None

            for item in report_generator:
                if item['type'] == 'report_data':
                    report_data = item['content']
                else:
                    yield item

            if report_data is None:
                yield {"type": "error", "content": "无法获取报告所需的数据。"}
                return

            # 使用 LLM 生成最终报告
            report_prompt = self.prompts.create_report_prompt(
                report_data['initial_query'], 
                report_data['results_summary']
            )
            for chunk in self.llm_client.text_chat(report_prompt, is_stream=True):
                yield {"type": "report", "content": chunk}

            self._save_task()
            yield {"type": "finished", "content": "报告已生成，任务已完成。"}

        except Exception as e:
            yield {"type": "error", "content": f"生成最终报告时发生错误: {str(e)}"}
            yield {"type": "error", "content": f"错误详情: {traceback.format_exc()}"}

    def _save_task(self):
        os.makedirs("output/succeed", exist_ok=True)
        query_summary = self._generate_query_summary()
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"output/succeed/{query_summary}_{timestamp}.pickle"
        
        self.plan_manager.save_to_file(filename)
        
        self.task_saved_path = filename

    def _generate_query_summary(self) -> str:
        query = self.plan_manager.get_plan_summary()
        prompt = f"请将以下查询总结为6个字以内的短语：\n{query}"
        response = self.llm_client.one_chat(prompt)
        summary = ''.join(c for c in response if c.isalnum() or c in ('-', '_'))
        return summary[:20]

    def _handle_schedule_run(self, query: str) -> Generator[Dict[str, Any], None, None]:
        if not self.task_saved_path:
            yield {"type": "error", "content": "计划尚未执行完毕，无法添加计划任务。"}
            return

        try:
            saved_plan = StepsPlanManager.load_from_file(self.task_saved_path)
        except Exception as e:
            yield {"type": "error", "content": f"无法加载保存的计划：{str(e)}"}
            return

        schedule_prompt = self.prompts.schedule_run_prompt(query, datetime.now().isoformat())
        schedule_response = self.llm_client.one_chat(schedule_prompt)

        try:
            schedule_params = self.plan_manager._extract_json_from_text(schedule_response)
            trigger = schedule_params.get('trigger')
            trigger_args = schedule_params.get('trigger_args', {})
        except json.JSONDecodeError:
            yield {"type": "error", "content": "无法解析调度参数。"}
            return

        if not trigger or not isinstance(trigger_args, dict):
            yield {"type": "error", "content": "无效的调度参数。"}
            return

        schedule = SchedulerManager()

        try:
            job = schedule.add_job(func=saved_plan.replay, trigger=trigger, **trigger_args)
            yield {"type": "message", "content": f"成功添加计划任务。任务ID: {job.id}"}
        except Exception as e:
            yield {"type": "error", "content": f"添加计划任务失败：{str(e)}"}

