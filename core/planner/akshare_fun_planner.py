import asyncio
from datetime import datetime
import os
import re
import traceback

from core.scheduler.schedule_manager import SchedulerManager
from ..akshare_doc.akshare_data_singleton import AKShareDataSingleton
from typing import Callable, List, Dict, Tuple, Union,Optional,Any
import json
from typing import Generator, Dict, Any, List, Optional
from ..llms.llm_factory import LLMFactory
from ..llms._llm_api_client import LLMApiClient
from ..interpreter.data_summarizer import DataSummarizer
from ..interpreter._sse_planner import SSEPlanner, RetrievalProvider
from .akshare_prompts import AksharePrompts
from ..llms.llm_factory import LLMFactory
from .akshare_retrieval_provider import AkshareRetrievalProvider
from .steps_plan_manager import StepsPlanManager
from .parse_query_as_command import create_command_parser
from .message import send_message

class AkshareFunPlanner(SSEPlanner):
    def __init__(self, max_retry=8, allow_yfinance: bool = False):
        self.llm_factory = LLMFactory()
        self.llm_client:LLMApiClient = self.llm_factory.get_instance()
        self.data_summarizer = DataSummarizer()
        self.retriever = AkshareRetrievalProvider()
        self.plan_manager = StepsPlanManager(max_retry=max_retry, allow_yfinance=allow_yfinance)
        self.prompts = AksharePrompts()
        self.task_saved_path:str = ""
        self.stop_every_step:bool = False
        self.command_parser = create_command_parser()
        self.plan_change_listeners: List[Callable[[Dict[str, Any]], None]] = []
        self.code_change_listeners: List[Callable[[Dict[str, Any]], None]] = []
        self.setting_change_listeners: List[Callable[[Dict[str, Any]], None]] = []
        self.command_send_listeners: List[Callable[[str,Optional[ Union[Dict[str, Any],str] ] ], None]] = []

    def add_plan_change_listener(self, listener: Callable[[Dict[str, Any]], None]):
        """添加计划变更监听器"""
        self.plan_change_listeners.append(listener)

    def add_code_change_listener(self, listener: Callable[[int, str], None]):
        """添加代码变更监听器"""
        self.code_change_listeners.append(listener)

    def add_setting_change_listener(self, listener: Callable[[Dict[str, Any]], None]):
        """添加设置变更监听器"""
        self.setting_change_listeners.append(listener)

    def add_command_send_listener(self, listener: Callable[[str,Optional[ Union[Dict[str, Any],str] ] ], None]):
        """添加命令发送监听器"""
        self.command_send_listeners.append(listener)

    def _notify_command_send(self, command: str, data:Optional[ Union[Dict[str, Any],str] ] = None):
        """通知所有命令发送监听器"""
        for listener in self.command_send_listeners:
            listener(command, data)

    def _notify_plan_change(self, new_plan: Dict[str, Any]):
        """通知所有计划变更监听器"""
        for listener in self.plan_change_listeners:
            listener(new_plan)

    def _notify_code_change(self, step_codes: dict):
        """通知所有代码变更监听器"""
        for listener in self.code_change_listeners:
            listener(step_codes)

    def _notify_setting_change(self, setting_data: Dict[str, Any]):
        """通知所有设置变更监听器"""
        for listener in self.setting_change_listeners:
            listener(setting_data)

    def set_max_retry(self, max_retry: int) -> Generator[Dict[str, Any], None, None]:
        self.plan_manager.max_retry = max_retry
        yield send_message(f"最大重试次数已设置为 {max_retry}")
        data = self._get_setting_data()
        self._notify_setting_change(data)

    def get_stop_every_step(self) -> bool:
        return self.stop_every_step

    def set_stop_every_step(self, stop_every_step: bool) -> Generator[Dict[str, Any], None, None]:
        self.stop_every_step = stop_every_step
        yield send_message(f"设置为每步停顿: {stop_every_step}")
        data = self._get_setting_data()
        self._notify_setting_change(data)

    def _get_setting_data(self)->Dict[str, Any]:
        return {
            "max_retry": self.plan_manager.max_retry,
            "allow_yfinance": self.plan_manager.allow_yfinance,
            "stop_every_step": self.stop_every_step
        }
    
    def _set_from_setting_data(self, setting_data: Dict[str, Any]):
        self.plan_manager.max_retry = setting_data.get("max_retry", 8)
        self.plan_manager.allow_yfinance = setting_data.get("allow_yfinance", False)
        self.stop_every_step = setting_data.get("stop_every_step", False)

    def set_current_plan(self, plan: Dict[str, Any]) -> None:
        self.plan_manager.current_plan = plan
    
    def get_current_plan(self) -> Dict[str, Any]:
        return self.plan_manager.current_plan
    
    def set_setp_codes(self, step_codes: Dict[str, str]) -> None:
        self.plan_manager.step_codes = step_codes
        
    def set_allow_yfinance(self, allow_yfinance: bool) -> None:
        self.plan_manager.allow_yfinance = allow_yfinance
        data = self._get_setting_data()
        self._notify_setting_change(data)

    def get_allow_yfinance(self) -> bool:
        return self.plan_manager.allow_yfinance

    def get_max_retry(self) -> int:
        return self.plan_manager.max_retry

    def show_step_code(self, step: int) -> Generator[Dict[str, Any], None, None]:
        code = self.plan_manager.get_step_code(step)
        if code:
            yield send_message(f"步骤 {step} 的代码：\n{code}", "code")
        else:
            yield send_message(f"步骤 {step} 的代码不存在", "error")

    def modify_step_code(self, step: int, query: str) -> Generator[Dict[str, Any], None, None]:
        yield from self.plan_manager.modify_step_code(step, query)
        new_code = self.plan_manager.get_step_code(step)
        if new_code:
            self._notify_code_change(self.plan_manager.step_codes)

    def reset(self) -> Generator[Dict[str, Any], None, None]:
        self.task_saved_path = ""
        self.plan_manager.reset()
        # 触发计划变更事件，传递空字典表示计划被清空
        self._notify_plan_change({})
        
        # 触发代码变更事件，传递 step=-1 和 空字符串 表示所有代码被删除
        self._notify_code_change(self.plan_manager.step_codes)
        yield send_message("所有数据已重置，可以重新开始。")
    
    def _parse_special_commands(self, query: str) -> Generator[Dict[str, Any], bool, None]:
        return self.command_parser.parse(query, self)

    def show_all_commands(self):
        commands = self.command_parser.get_help()
        for cmd, help_text in commands:
            print(f"{cmd}: {help_text}")

    def plan_chat(self, query: str) -> Generator[Dict[str, Any], None, None]:
        command_handled = yield from self._parse_special_commands(query)
        if command_handled:
            return

        if self.plan_manager.current_plan == {}:
            yield from self.plan_manager.create_plan(query)
            if self.plan_manager.current_plan:
                self._notify_plan_change(self.plan_manager.current_plan)
        else:
            yield from self.plan_manager.modify_plan(query)
            if self.plan_manager.current_plan:
                self._notify_plan_change(self.plan_manager.current_plan)

        if self.plan_manager.current_plan:
            yield send_message("计划生成完毕。请检查计划并输入'确认计划'来开始执行，或继续修改计划。")

        if self.plan_manager.is_plan_confirmed:
            yield from self.stream_progress()

    def handle_confirm_plan(self) -> Generator[Dict[str, Any], None, None]:
        if not self.plan_manager.current_plan:
            yield send_message("没有可确认的计划。请先创建一个计划。", "error")
            return

        self.plan_manager.is_plan_confirmed = True
        yield send_message("计划已确认。开始执行计划。")
        yield from self.stream_progress()

    def stream_progress(self) -> Generator[Dict[str, Any], None, None]:
        while self.plan_manager.current_step_number < self.plan_manager.total_steps:
            self.plan_manager.clear_history()
            current_step = self.plan_manager.get_current_step()
            total_steps = self.plan_manager.total_steps
            step_number = self.plan_manager.current_step_number + 1

            yield send_message(json.dumps({
                "step": step_number,
                "total_steps": total_steps,
                "description": current_step['description'],
                "progress": step_number / total_steps
            },ensure_ascii=False), "progress")

            yield from self.step()

            if self.stop_every_step:
                yield send_message("步骤执行完成。等待用户确认继续。", "pause")
                return

        yield send_message("所有步骤已完成。正在生成最终报告...")
        yield from self.get_final_report()

    def redo(self)-> Generator[Dict[str, Any], None, None]:
        self.plan_manager.current_step_number = 0
        self.plan_manager.is_plan_confirmed = False
        while self.plan_manager.current_step_number < self.plan_manager.total_steps:
            self.plan_manager.clear_history()
            yield from self.plan_manager.redo_step()


    def step(self) -> Generator[Dict[str, Any], None, None]:
        try:
            yield from self.plan_manager.step()
            current_step = self.plan_manager.current_step_number
            new_code = self.plan_manager.get_step_code(current_step)
            if new_code:
                self._notify_code_change(self.plan_manager.step_codes)
        except Exception as e:
            yield send_message(f"执行步骤时发生错误: {str(e)}", "error")
            #yield from self.handle_error(e)

    def handle_error(self, error: Exception) -> Generator[Dict[str, Any], None, None]:
        error_message = str(error)
        yield send_message(error_message, "error")
        
        fix_prompt = f"发生了一个错误：{error_message}。请提供解决方案或下一步建议。"
        for chunk in self.llm_client.text_chat(fix_prompt, is_stream=True):
            yield send_message(chunk, "plan")

    def get_final_report(self) -> Generator[Dict[str, Any], None, None]:
        reporter = self.llm_factory.get_reporter()
        try:
            report_generator = self.plan_manager.get_final_report()
            report_data = None

            for item in report_generator:
                if item['type'] == 'report_data':
                    report_data = item['content']
                else:
                    yield send_message(item['content'], item['type'])

            if report_data is None:
                yield send_message("无法获取报告所需的数据。", "error")
                return

            report_prompt = self.prompts.create_report_prompt(
                report_data['initial_query'], 
                report_data['results_summary']
            )
            for chunk in reporter.text_chat(report_prompt, is_stream=True):
                yield send_message(chunk, "report")

            self._save_task()
            yield send_message("报告已生成，任务已完成。", "finished")

        except Exception as e:
            yield send_message(f"生成最终报告时发生错误: {str(e)}", "error")
            yield send_message(f"错误详情: {traceback.format_exc()}", "error")

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
            yield send_message("计划尚未执行完毕，无法添加计划任务。", "error")
            return

        try:
            saved_plan = StepsPlanManager.load_from_file(self.task_saved_path)
        except Exception as e:
            yield send_message(f"无法加载保存的计划：{str(e)}", "error")
            return

        schedule_prompt = self.prompts.schedule_run_prompt(query, datetime.now().isoformat())
        schedule_response = self.llm_client.one_chat(schedule_prompt)

        try:
            schedule_params = self.plan_manager._extract_json_from_text(schedule_response)
            trigger = schedule_params.get('trigger')
            trigger_args = schedule_params.get('trigger_args', {})
        except json.JSONDecodeError:
            yield send_message("无法解析调度参数。", "error")
            return

        if not trigger or not isinstance(trigger_args, dict):
            yield send_message("无效的调度参数。", "error")
            return

        schedule = SchedulerManager()
        def sync_wrapper():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            task = loop.create_task(saved_plan.replay())
            return loop.run_until_complete(task) 
        try:
            job = schedule.add_job(func=sync_wrapper, trigger=trigger, **trigger_args)
            yield send_message(f"成功添加计划任务。任务ID: {job.id}")
        except Exception as e:
            yield send_message(f"添加计划任务失败：{str(e)}", "error")

    def export(self) -> Generator[Dict[str, Any], None, None]:
        import uuid
        output_dir = "./output/code"
        
        # Check if the output directory exists, if not create it
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            yield send_message(f"创建目录 {output_dir}")

        # Create a new directory with a UUID4 name
        export_dir = os.path.join(output_dir, str(uuid.uuid4()))
        os.makedirs(export_dir)
        yield send_message(f"创建导出目录: {export_dir}")

        # Export the plan as plan.json
        plan_path = os.path.join(export_dir, "plan.json")
        with open(plan_path, 'w', encoding='utf-8') as f:
            json.dump(self.plan_manager.current_plan, f, ensure_ascii=False, indent=2)
        yield send_message(f"导出 plan 到: {plan_path}")

        # Export step codes
        for step_number, code in self.plan_manager.step_codes.items():
            code_path = os.path.join(export_dir, f"step_code_{step_number}.py")
            with open(code_path, 'w', encoding='utf-8') as f:
                f.write(code)
            yield send_message(f"导出步骤 {step_number} 代码到: {code_path}")

        yield send_message("导出成功.")
        
        def validate_plan(self,plan)-> Tuple[str, bool]:
            return self.plan_manager.validate_plan(plan)
