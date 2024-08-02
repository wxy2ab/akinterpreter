import asyncio
from datetime import datetime
import os
import json
from typing import Callable, List, Dict, Tuple, Union, Optional, Any, Generator
from core.scheduler.schedule_manager import SchedulerManager
from .message import send_message
from .parse_query_as_command import create_command_parser
from .blueprint import BluePrint
from .step_data import StepData

class AkshareBPPlanner:
    def __init__(self, max_retry=8):
        self.blueprint = BluePrint()
        self.task_saved_path: str = ""
        self.stop_every_step: bool = False
        self.command_parser = create_command_parser()
        self.plan_change_listeners: List[Callable[[Dict[str, Any]], None]] = []
        self.code_change_listeners: List[Callable[[Dict[str, Any]], None]] = []
        self.setting_change_listeners: List[Callable[[Dict[str, Any]], None]] = []
        self.command_send_listeners: List[Callable[[str, Optional[Union[Dict[str, Any], str]]], None]] = []

    def add_plan_change_listener(self, listener: Callable[[Dict[str, Any]], None]):
        self.plan_change_listeners.append(listener)

    def add_code_change_listener(self, listener: Callable[[int, str], None]):
        self.code_change_listeners.append(listener)

    def add_setting_change_listener(self, listener: Callable[[Dict[str, Any]], None]):
        self.setting_change_listeners.append(listener)

    def add_command_send_listener(self, listener: Callable[[str, Optional[Union[Dict[str, Any], str]]], None]):
        self.command_send_listeners.append(listener)

    def _notify_command_send(self, command: str, data: Optional[Union[Dict[str, Any], str]] = None):
        for listener in self.command_send_listeners:
            listener(command, data)

    def _notify_plan_change(self, new_plan: Dict[str, Any]):
        for listener in self.plan_change_listeners:
            listener(new_plan)

    def _notify_code_change(self, step_codes: dict):
        for listener in self.code_change_listeners:
            listener(step_codes)

    def _notify_setting_change(self, setting_data: Dict[str, Any]):
        for listener in self.setting_change_listeners:
            listener(setting_data)

    def set_max_retry(self, max_retry: int) -> Generator[Dict[str, Any], None, None]:
        self.blueprint.max_retry = max_retry
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

    def _get_setting_data(self) -> Dict[str, Any]:
        return {
            "max_retry": self.blueprint.max_retry,
            "stop_every_step": self.stop_every_step
        }

    def _set_from_setting_data(self, setting_data: Dict[str, Any]):
        self.blueprint.max_retry = setting_data.get("max_retry", 8)
        self.stop_every_step = setting_data.get("stop_every_step", False)

    def get_current_plan(self) -> Dict[str, Any]:
        return self.blueprint.blueprint.to_dict() if self.blueprint.blueprint else {}

    def get_max_retry(self) -> int:
        return self.blueprint.max_retry

    def show_step_code(self, step: int) -> Generator[Dict[str, Any], None, None]:
        code = self.blueprint.step_data.get_step_code(step)
        if code:
            yield send_message(f"步骤 {step} 的代码：\n{code}", "code")
        else:
            yield send_message(f"步骤 {step} 的代码不存在", "error")

    def modify_step_code(self, step: int, query: str) -> Generator[Dict[str, Any], None, None]:
        # 这里需要实现代码修改的逻辑，可能需要调用blueprint_coder的方法
        # 暂时使用一个简单的实现
        new_code = f"# Modified code for step {step}\n# Query: {query}\n# TODO: Implement actual code modification"
        self.blueprint.step_data.set_step_code(step, new_code)
        yield send_message(f"步骤 {step} 的代码已更新。", "message")
        self._notify_code_change({step: new_code})

    def reset(self) -> Generator[Dict[str, Any], None, None]:
        self.task_saved_path = ""
        self.blueprint.clear()
        self._notify_plan_change({})
        self._notify_code_change({})
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

        if self.blueprint.blueprint is None:
            yield from self.blueprint.build_blueprint(query)
            if self.blueprint.blueprint:
                self._notify_plan_change(self.blueprint.blueprint.to_dict())
        else:
            yield from self.blueprint.modify_blueprint(query, self.blueprint.blueprint.to_dict())
            if self.blueprint.blueprint:
                self._notify_plan_change(self.blueprint.blueprint.to_dict())

        if self.blueprint.blueprint:
            yield send_message("计划生成完毕。请检查计划并输入'确认计划'来开始执行，或继续修改计划。")

    def handle_confirm_plan(self) -> Generator[Dict[str, Any], None, None]:
        if not self.blueprint.blueprint:
            yield send_message("没有可确认的计划。请先创建一个计划。", "error")
            return

        yield send_message("计划已确认。开始执行计划。")
        yield from self.stream_progress()

    def stream_progress(self) -> Generator[Dict[str, Any], None, None]:
        total_steps = len(self.blueprint.blueprint)
        for step_number, step in enumerate(self.blueprint.blueprint, start=1):
            yield send_message(json.dumps({
                "step": step_number,
                "total_steps": total_steps,
                "description": step.description,
                "progress": step_number / total_steps
            }, ensure_ascii=False), "progress")

            yield from self.blueprint.generate_step(step)

            if self.stop_every_step:
                yield send_message("步骤执行完成。等待用户确认继续。", "pause")
                return

        yield send_message("所有步骤已完成。正在生成最终报告...")
        yield from self.get_final_report()

    def step(self) -> Generator[Dict[str, Any], None, None]:
        try:
            current_step = next(iter(self.blueprint.blueprint))  # 获取第一个步骤
            yield from self.blueprint.generate_step(current_step)
            new_code = self.blueprint.step_data.get_step_code(current_step.step_number)
            if new_code:
                self._notify_code_change({current_step.step_number: new_code})
        except Exception as e:
            yield send_message(f"执行步骤时发生错误: {str(e)}", "error")

    def get_final_report(self) -> Generator[Dict[str, Any], None, None]:
        try:
            yield from self.blueprint.final_report()
            self._save_task()
            yield send_message("报告已生成，任务已完成。", "finished")
        except Exception as e:
            yield send_message(f"生成最终报告时发生错误: {str(e)}", "error")

    def _save_task(self):
        os.makedirs("output/succeed", exist_ok=True)
        query_summary = self._generate_query_summary()
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"output/succeed/{query_summary}_{timestamp}.pickle"
        self.blueprint.save_to_file(filename)
        self.task_saved_path = filename

    def _generate_query_summary(self) -> str:
        query = self.blueprint.blueprint.query_summary if self.blueprint.blueprint else ""
        return query[:20]

    def _handle_schedule_run(self, query: str) -> Generator[Dict[str, Any], None, None]:
        if not self.task_saved_path:
            yield send_message("计划尚未执行完毕，无法添加计划任务。", "error")
            return

        try:
            saved_blueprint = BluePrint.load_from_file(self.task_saved_path)
        except Exception as e:
            yield send_message(f"无法加载保存的计划：{str(e)}", "error")
            return

        schedule = SchedulerManager()
        def sync_wrapper():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            task = loop.create_task(saved_blueprint.generate_and_execute_all())
            return loop.run_until_complete(task) 

        try:
            job = schedule.add_job(func=sync_wrapper, trigger='interval', minutes=5)  # 示例：每5分钟执行一次
            yield send_message(f"成功添加计划任务。任务ID: {job.id}")
        except Exception as e:
            yield send_message(f"添加计划任务失败：{str(e)}", "error")

    def export(self) -> Generator[Dict[str, Any], None, None]:
        import uuid
        output_dir = "./output/code"
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            yield send_message(f"创建目录 {output_dir}")

        export_dir = os.path.join(output_dir, str(uuid.uuid4()))
        os.makedirs(export_dir)
        yield send_message(f"创建导出目录: {export_dir}")

        plan_path = os.path.join(export_dir, "plan.json")
        with open(plan_path, 'w', encoding='utf-8') as f:
            json.dump(self.blueprint.blueprint.to_dict(), f, ensure_ascii=False, indent=2)
        yield send_message(f"导出 plan 到: {plan_path}")

        for step in self.blueprint.blueprint:
            code = self.blueprint.step_data.get_step_code(step.step_number)
            if code:
                code_path = os.path.join(export_dir, f"step_code_{step.step_number}.py")
                with open(code_path, 'w', encoding='utf-8') as f:
                    f.write(code)
                yield send_message(f"导出步骤 {step.step_number} 代码到: {code_path}")

        yield send_message("导出成功.")

    def validate_plan(self, plan) -> Tuple[str, bool]:
        # 实现计划验证逻辑
        return "", True  # 示例返回值，表示验证通过