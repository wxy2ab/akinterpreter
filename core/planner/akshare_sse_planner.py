from datetime import datetime
import os
import re
from ..akshare_doc.akshare_data_singleton import AKShareDataSingleton
from typing import List, Dict, Tuple, Union
import json
from typing import Generator, Dict, Any, List, Optional
from ..llms.llm_factory import LLMFactory
from ..llms._llm_api_client import LLMApiClient
from ..interpreter.sse_code_runner import SSECodeRunner
from ..interpreter.data_summarizer import DataSummarizer
from ..interpreter._sse_planner import SSEPlanner, RetrievalProvider
from .akshare_prompts import AksharePrompts
from .akshare_retrieval_provider import AkshareRetrievalProvider

class AkshareSSEPlanner(SSEPlanner):
    def __init__(self, max_retry=8, allow_yfinance: bool = False):
        self.llm_factory = LLMFactory()
        self.llm_client: LLMApiClient = self.llm_factory.get_instance()
        self.code_runner = SSECodeRunner()
        self.data_summarizer = DataSummarizer()
        self.retriever = self.get_retrieval_provider()
        self.reset()
        self.prompts = AksharePrompts()
        self.max_retry = max_retry
        self.allow_yfinance = allow_yfinance
        self.step_codes = {}
        self.task_finished:bool= False
        self.task_saved_path:str = ""

    def get_new_llm_client(self) -> LLMApiClient:
        return self.llm_factory.get_instance()
    
    def get_retrieval_provider(self) -> RetrievalProvider:
        return AkshareRetrievalProvider()

    def _parse_special_commands(self, query: str) -> Generator[Dict[str, Any], bool, None]:
        confirm_keywords = ["确认计划", "确认", "开始", "开始执行", "运行", "执行", "没问题", "没问题了", "执行计划"]
        reset_keywords = ["重来", "清除", "再来一次", "重新开始", "重置", "清空", "清空所有", "清空数据", "清空状态", "清空计划", "清空所有数据", "清空所有状态", "清空所有计划", "清空所有数据和状态", "清空所有数据和计划", "清空所有状态和计划"]

        if query.lower().startswith("schedule_run "):
            if not self.task_saved_path:
                yield {"type": "error", "content": "没有可运行的已保存任务。请先保存任务。"}
                return True

            schedule_query = query[len("schedule_run "):]
            yield from self._handle_schedule_run(schedule_query)
            return True

        if query.lower().startswith("set_max_retry="):
            try:
                new_max_retry = int(query.split("=")[1])
                self.max_retry = new_max_retry
                yield {"type": "message", "content": f"已将 max_retry 设置为 {new_max_retry}"}
                return True
            except ValueError:
                yield {"type": "error", "content": "无效的 max_retry 值。请输入一个整数。"}
                return True

        if query.lower().startswith("set_allow_yfinance="):
            value = query.split("=")[1].lower()
            if value in ["true", "false"]:
                self.allow_yfinance = value == "true"
                yield {"type": "message", "content": f"已将 allow_yfinance 设置为 {self.allow_yfinance}"}
            else:
                yield {"type": "error", "content": "无效的 allow_yfinance 值。请使用 true 或 false。"}
            return True

        if query.lower() == "show_config":
            config = f"当前配置：\nmax_retry: {self.max_retry}\nallow_yfinance: {self.allow_yfinance}"
            yield {"type": "message", "content": config}
            return True

        if query.lower() in reset_keywords:
            self.reset()
            yield {"type": "message", "content": "已重置所有数据，请重新开始。"}
            return True

        if query.lower() in confirm_keywords:
            if not self.current_plan:
                yield {"type": "error", "content": "没有可确认的计划。请先创建一个计划。"}
            else:
                yield from self.handle_confirm_plan()
            return True

        if query.lower().startswith("show_step_code="):
            try:
                step = int(query.split("=")[1])
                yield from self.show_step_code(step)
            except ValueError:
                yield {"type": "error", "content": "无效的步骤编号。请输入一个整数。"}
            return True

        if query.lower().startswith("modify_step_code="):
            try:
                parts = query.split("=", 1)[1].split(" ", 1)
                step = int(parts[0])
                modification_query = parts[1] if len(parts) > 1 else ""
                yield from self.modify_step_code(step, modification_query)
            except ValueError:
                yield {"type": "error", "content": "无效的步骤编号。请输入一个整数。"}
            except IndexError:
                yield {"type": "error", "content": "无效的命令格式。请使用 'modify_step_code=[step] [query]'。"}
            return True

        return False

    def _handle_schedule_run(self, schedule_query: str) -> Generator[Dict[str, Any], None, None]:
        import pytz
        from ..scheduler.schedule_manager import SchedulerManager
        import asyncio
        
        current_time = datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
        prompt = self.prompts.schedule_run_prompt(schedule_query, current_time)

        llm_client = self.get_new_llm_client()
        response = llm_client.one_chat(prompt)

        try:
            parsed_response = json.loads(response)
            if "error" in parsed_response:
                yield {"type": "error", "content": parsed_response["error"]}
                return

            trigger = parsed_response["trigger"]
            trigger_args = parsed_response["trigger_args"]

            manager = SchedulerManager()

            def run_task():
                planner = AkshareSSEPlanner.load_from_file(self.task_saved_path)
                asyncio.run(planner.replay())

            job = manager.add_job(func=run_task, trigger=trigger, **trigger_args)

            if job:
                yield {"type": "message", "content": f"任务已成功调度。触发器类型: {trigger}, 参数: {trigger_args}"}
            else:
                yield {"type": "error", "content": "任务调度失败。"}

        except json.JSONDecodeError:
            yield {"type": "error", "content": "LLM 响应解析失败。无法调度任务。"}
        except Exception as e:
            yield {"type": "error", "content": f"调度任务时发生错误: {str(e)}"}

    def show_step_code(self, step: int) -> Generator[Dict[str, Any], None, None]:
        if str(step - 1) not in self.step_codes:
            yield {"type": "error", "content": f"步骤 {step} 的代码不存在。"}
        else:
            code = self.step_codes[str(step - 1)]
            yield {"type": "code", "content": f"步骤 {step} 的代码：\n{code}"}

    def modify_step_code(self, step: int, query: str) -> Generator[Dict[str, Any], None, None]:
        if str(step - 1) not in self.step_codes:
            yield {"type": "error", "content": f"步骤 {step} 的代码不存在。"}
            return

        current_code = self.step_codes[str(step - 1)]
        prompt = self.prompts.modify_step_code_prompt(current_code, query)

        llm_client = self.get_new_llm_client()
        modified_code = ""
        for chunk in llm_client.text_chat(prompt, is_stream=True):
            modified_code += chunk
            yield {"type": "code_modification_progress", "content": chunk}

        self.step_codes[str(step - 1)] = modified_code.strip()
        yield {"type": "message", "content": f"步骤 {step} 的代码已更新。"}
        yield {"type": "code", "content": f"更新后的代码：\n{modified_code.strip()}"}

    def plan_chat(self, query: str) -> Generator[Dict[str, Any], None, None]:
        # 首先尝试解析特殊命令
        command_handled = False
        command_generator = self._parse_special_commands(query)
        try:
            while True:
                command_result = next(command_generator)
                yield command_result
        except StopIteration as e:
            command_handled = e.value

        if command_handled:
            return

        # 如果不是特殊命令，则继续原有的计划创建或修改逻辑
        prompt = self._create_plan_prompt(query) if self.current_plan is None else self._create_modify_plan_prompt(query)
        
        plan_text = ""
        for chunk in self.llm_client.text_chat(prompt, is_stream=True):
            plan_text += chunk
            yield {"type": "plan", "content": chunk}
        
        try:
            plan = self._extract_json_from_text(plan_text)
            self.current_plan = plan
            self.total_steps = len(self.current_plan['steps'])
            yield {"type": "plan", "content": self.current_plan}
            yield {"type": "message", "content": "计划生成完毕。请检查计划并输入'确认计划'来开始执行，或继续修改计划。"}
        except json.JSONDecodeError:
            yield {"type": "error", "content": "无法创建有效的计划。请重试。"}

    def _create_plan_prompt(self, query: str) -> str:
        categories = self.retriever.get_categories()
        return self.prompts.create_plan_prompt(query, categories)

    def _create_modify_plan_prompt(self, query: str) -> str:
        return self.prompts.modify_plan_prompt(query, self.current_plan)

    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            json_str = json_match.group()
            return json.loads(json_str)
        raise json.JSONDecodeError("No valid JSON found in the text", text, 0)

    def handle_confirm_plan(self) -> Generator[Dict[str, Any], None, None]:
        if not self.current_plan:
            yield {"type": "error", "content": "没有可确认的计划。请先创建一个计划。"}
            return

        self.confirm_plan()
        yield {"type": "message", "content": "计划已确认。开始执行计划。"}
        yield from self.execute_plan()

    def confirm_plan(self) -> None:
        if not self.current_plan:
            raise ValueError("没有可确认的计划。请先创建一个计划。")
        self.current_step = 0
        self.is_plan_confirmed = True

    def execute_plan(self) -> Generator[Dict[str, Any], None, None]:
        if not self.is_plan_confirmed:
            yield {"type": "error", "content": "计划尚未确认。请先确认计划。"}
            return

        yield from self.stream_progress()

    def step(self) -> Generator[Dict[str, Any], None, None]:
        if not self.current_plan:
            yield {"type": "error", "content": "没有可用的计划。请先创建并确认一个计划。"}
            return

        if self.current_step >= len(self.current_plan['steps']):
            yield {"type": "message", "content": "所有步骤已完成。"}
            return

        current_step = self.current_plan['steps'][self.current_step]
        yield {"type": "message", "content": f"执行步骤 {self.current_step + 1}: {current_step['description']}"}

        code_generator = self._generate_code(current_step)
        full_code = ""
        for code_chunk in code_generator:
            if isinstance(code_chunk, dict) and code_chunk["type"] == "code_generation_progress":
                yield code_chunk
            elif isinstance(code_chunk, str):
                full_code += code_chunk

        if not full_code:
            yield {"type": "error", "content": "未能生成有效的代码。"}
            return

        yield {"type": "code_generation", "content": full_code}

        max_attempts = self.max_retry
        for attempt in range(max_attempts):
            try:
                if current_step['type'] == 'data_retrieval':
                    yield from self.execute_data_retrieval(full_code, current_step)
                elif current_step['type'] == 'data_analysis':
                    yield from self.execute_data_analysis(full_code, current_step)
                else:
                    raise Exception(f"未知的步骤类型: {current_step['type']}")

                self.step_codes[self.current_step] = full_code
                break
            except Exception as e:
                if attempt < max_attempts - 1:
                    yield {"type": "code_fix", "content": f"第 {attempt + 1} 次尝试失败。错误：{str(e)}。正在尝试修复代码。"}
                    fix_generator = self._fix_code(full_code, str(e))
                    full_code = "".join(chunk for chunk in fix_generator if isinstance(chunk, str))
                else:
                    yield {"type": "error", "content": f"在 {max_attempts} 次尝试后仍无法执行代码。最后的错误：{str(e)}"}

        self.current_step += 1

    def execute_data_retrieval(self, code: str, step: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        global_vars = self.step_vars.copy()
        global_vars['llm_client'] = self.get_new_llm_client()

        updated_vars = {}
        for event in self.code_runner.run_sse(code, global_vars):
            if event['type'] == 'output':
                yield {"type": "code_execution", "content": event['content']}
            elif event['type'] == 'error':
                yield {"type": "error", "content": event['content']}
                raise Exception(event['content'])
            elif event['type'] == 'variables':
                updated_vars = event['content']

        if step['save_data_to'] in updated_vars:
            data = updated_vars[step['save_data_to']]
            self.step_vars[step['save_data_to']] = data
            
            # 生成数据摘要
            summary = self.data_summarizer.get_data_summary(data)
            self.step_vars[f"{step['save_data_to']}_summary"] = summary
            
            result = f"数据已保存到 {step['save_data_to']}"
            self.execution_results.append({
                "step": self.current_step,
                "type": "data_retrieval",
                "result": result
            })
            yield {"type": "code_execution", "content": result}
            yield {"type": "summary", "content": f"数据摘要: {summary}"}
        else:
            error_msg = f"执行代码未产生预期的 '{step['save_data_to']}' 变量。可用变量: {list(updated_vars.keys())}"
            yield {"type": "error", "content": error_msg}
            raise Exception(error_msg)

    def execute_data_analysis(self, code: str, step: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        global_vars = self.step_vars.copy()
        global_vars['llm_client'] = self.get_new_llm_client()

        updated_vars = {}
        for event in self.code_runner.run_sse(code, global_vars):
            if event['type'] == 'output':
                yield {"type": "code_execution", "content": event['content']}
            elif event['type'] == 'error':
                yield {"type": "error", "content": event['content']}
                raise Exception(event['content'])
            elif event['type'] == 'variables':
                updated_vars = event['content']

        # 处理 analysis_result
        if 'analysis_result' in updated_vars:
            result = updated_vars['analysis_result']
            self.step_vars[f"analysis_result_{self.current_step}"] = result
            self.execution_results.append({
                "step": self.current_step,
                "type": "data_analysis",
                "result": result
            })
            yield {"type": "code_execution", "content": "分析结果已生成"}

        # 处理 save_data_to（如果存在）
        if 'save_data_to' in step:
            save_data_to = step['save_data_to']
            if save_data_to in updated_vars:
                data = updated_vars[save_data_to]
                self.step_vars[save_data_to] = data
                
                # 生成数据摘要
                summary = self.data_summarizer.get_data_summary(data)
                self.step_vars[f"{save_data_to}_summary"] = summary
                
                result = f"数据已保存到 {save_data_to}"
                self.execution_results.append({
                    "step": self.current_step,
                    "type": "data_analysis_save",
                    "result": result
                })
                yield {"type": "code_execution", "content": result}
                yield {"type": "summary", "content": f"数据摘要: {summary}"}
            else:
                warning_msg = f"警告: 执行代码未产生预期的 '{save_data_to}' 变量。可用变量: {list(updated_vars.keys())}"
                yield {"type": "warning", "content": warning_msg}

        if 'analysis_result' not in updated_vars and ('save_data_to' not in step or step['save_data_to'] not in updated_vars):
            error_msg = f"执行代码未产生预期的结果。可用变量: {list(updated_vars.keys())}"
            yield {"type": "error", "content": error_msg}
            raise Exception(error_msg)

    def execute_code(self, code: str) -> Dict[str, Any]:
        global_vars = self.step_vars.copy()
        global_vars['llm_client'] = self.get_new_llm_client()  # 为每次执行提供新的 LLMApiClient 实例
        output, error = self.code_runner.run(code, global_vars)
        if error:
            raise Exception(error)
        return {"output": output, "variables": global_vars}

    def stream_progress(self) -> Generator[Dict[str, Any], None, None]:
        while self.current_step < self.total_steps:
            yield {
                "type": "progress",
                "content": {
                    "step": self.current_step + 1,
                    "total_steps": self.total_steps,
                    "description": self.current_plan['steps'][self.current_step]['description'],
                    "progress": (self.current_step + 1) / self.total_steps
                }
            }
            yield from self.step()

        yield from self.get_final_report()

    def handle_error(self, error: Exception) -> Generator[Dict[str, Any], None, None]:
        error_message = str(error)
        yield {"type": "error", "content": error_message}
        
        fix_prompt = f"发生了一个错误：{error_message}。请提供解决方案或下一步建议。"
        for chunk in self.llm_client.text_chat(fix_prompt, is_stream=True):
            yield {"type": "solution", "content": chunk}

    def save_state(self) -> Dict[str, Any]:
        return {
            "current_plan": self.current_plan,
            "execution_results": self.execution_results,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "is_plan_confirmed": self.is_plan_confirmed
        }

    def load_state(self, state: Dict[str, Any]) -> None:
        self.current_plan = state.get("current_plan")
        self.execution_results = state.get("execution_results", [])
        self.current_step = state.get("current_step", 0)
        self.total_steps = state.get("total_steps", 0)
        self.is_plan_confirmed = state.get("is_plan_confirmed", False)

    def _generate_code(self, step: Dict[str, Any]) -> Generator[Union[Dict[str, Any], str], None, None]:
        if step['type'] == 'data_retrieval':
            yield from self._generate_data_retrieval_code(step)
        elif step['type'] == 'data_analysis':
            yield from self._generate_data_analysis_code(step)
        else:
            yield {"type": "error", "content": f"错误：未知的步骤类型 {step['type']}"}

    def _generate_data_retrieval_code(self, step: Dict[str, Any]) -> Generator[Union[Dict[str, Any], str], None, None]:
        category = step['data_category']
        
        # 从选定类别中选择函数
        selected_functions = yield from self._select_functions_from_category(step, category)
        
        # 生成代码
        extracted_code = ""
        for item in self._generate_code_for_functions(step, selected_functions):
            if isinstance(item, dict):
                yield item  # 传递进度信息
            elif isinstance(item, str):
                extracted_code = item  # 保存提取的代码
        
        # yield 最终的代码
        yield extracted_code

    def _extract_code(self, content: str) -> str:
        # 使用正则表达式提取代码块
        code_match = re.search(r'```python(.*?)```', content, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        else:
            # 如果没有找到代码块，返回整个内容（假设整个内容都是代码）
            return content.strip()

    def _generate_code_for_functions(self, step: Dict[str, Any], functions: List[str]) -> Generator[Union[Dict[str, Any], str], None, None]:
        function_docs = self.retriever.get_specific_doc(functions)

        code_prompt = self.prompts.generate_code_for_functions_prompt(step, function_docs)

        llm_client = self.get_new_llm_client()
        full_content = ""
        for chunk in llm_client.text_chat(code_prompt, is_stream=True):
            full_content += chunk
            yield {"type": "code_generation_progress", "content": chunk}
        
        # 提取代码块
        extracted_code = self._extract_code(full_content)
        
        # 首先yield完整的生成内容
        yield {"type": "code_generation", "content": full_content}
        
        # 然后yield提取出的代码
        yield extracted_code

    def _select_data_category(self, step: Dict[str, Any], categories: Dict[str, str]) -> Generator[str, None, None]:
        category_prompt = self.prompts.select_data_category_prompt(step, categories)
        
        llm_client = self.get_new_llm_client()
        response = yield from llm_client.text_chat(category_prompt, is_stream=True)
        selected_category = response.strip()
        yield {"type": "category_selection", "content": f"已选择数据类别：{selected_category}"}
        return selected_category

    def _select_functions_from_category(self, step: Dict[str, Any], category: str) -> Generator[List[str], None, None]:
        functions = self.retriever.get_functions([category])
        function_prompt = self.prompts.select_functions_from_category_prompt(step, functions[category])
        
        llm_client = self.get_new_llm_client()
        full_response = ""
        for chunk in llm_client.text_chat(function_prompt, is_stream=True):
            full_response += chunk
            yield {"type": "function_selection_progress", "content": chunk}

        selected_functions = [func.strip() for func in full_response.split(',')]
        yield {"type": "function_selection", "content": f"已选择函数：{', '.join(selected_functions)}"}
        return selected_functions

    def _generate_data_analysis_code(self, step: Dict[str, Any]) -> Generator[Union[Dict[str, Any], str], None, None]:
        data_summaries = {
            data_var: self.step_vars.get(f"{data_var}_summary", "数据摘要不可用")
            for data_var in step['required_data']
        }
        
        code_prompt = self.prompts.generate_data_analysis_code_prompt(step, data_summaries,self.allow_yfinance)

        llm_client = self.get_new_llm_client()
        full_code = ""
        for chunk in llm_client.text_chat(code_prompt, is_stream=True):
            full_code += chunk
            yield {"type": "code_generation_progress", "content": chunk}
        
        code = self._extract_code(full_code)
        yield code

    def _fix_code(self, code: str, error: str) -> Generator[str, None, None]:
        fix_prompt = self.prompts.fix_code_prompt(code, error)
        full_code = ""
        for chunk in self.llm_client.text_chat(fix_prompt, is_stream=True):
            full_code += chunk
            yield {"type": "code_fix_progress", "content": chunk}
        
        fixed_code = self._extract_code(full_code)
        yield fixed_code

    def reset(self) -> None:
        self.task_finished=False
        self.current_step = 0
        self.total_steps = 0
        self.is_plan_confirmed = False
        self.current_plan = None
        self.task_saved_path = ""
        self.execution_results = []
        self.step_codes = {}
        self.step_vars: Dict[str, Any] = {
            "llm_factory": self.llm_factory,
            "code_runner": self.code_runner,
            "data_summarizer": self.data_summarizer
        }

    def get_final_report(self) -> Generator[Dict[str, Any], None, None]:
        if not self.execution_results:
            yield {"type": "message", "content": "没有可报告的结果。请先执行计划。"}
            return

        # 收集所有分析结果
        analysis_results = []
        for result in self.execution_results:
            if result['type'] == 'data_analysis':
                analysis_results.append({
                    "task": self.current_plan['steps'][result['step']]['description'],
                    "result": result['result']
                })

        if not analysis_results:
            yield {"type": "message", "content": "未找到任何分析结果。请检查数据分析步骤是否正确执行。"}
            return

        prompt = self._create_report_prompt(analysis_results)
        for chunk in self.llm_client.text_chat(prompt, is_stream=True):
            yield {"type": "report", "content": chunk}
        
        self._save_code_after_report()
        self.task_finished = True
        #yield {"type": "finished", "content": "报告已生成，计划已重置。可以重新开始新的任务啦！"}

    def _create_report_prompt(self, analysis_results: List[Dict[str, str]]) -> str:
        initial_query = self.current_plan.get('query_summary', '未提供初始查询')
        
        results_summary = "\n\n".join([
            f"任务: {result['task']}\n结果: {result['result']}"
            for result in analysis_results
        ])

        return self.prompts.create_report_prompt(initial_query, results_summary)

    def _save_code_after_report(self):
        # 确保输出目录存在
        os.makedirs("output/succeed", exist_ok=True)

        # 生成文件名
        query_summary = self._generate_query_summary()
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"output/succeed/{query_summary}_{timestamp}.json"

        # 保存代码
        self.save_to_file(filename)

        self.task_saved_path = filename
        
        return {"type": "message", "content": f"代码已保存到 {filename}"}

    def _generate_query_summary(self) -> str:
        # 使用 LLM 生成查询总结
        query = self.current_plan.get('query_summary', '未知查询')
        prompt = f"请将以下查询总结为6个字以内的短语：\n{query}"
        response = self.llm_client.one_chat(prompt)
        
        # 清理响应，确保它是一个有效的文件名
        summary = ''.join(c for c in response if c.isalnum() or c in ('-', '_'))
        return summary[:20]  # 限制长度为20个字符

    def save_to_file(self, filename: str):
        """保存计划和代码到文件"""
        data = {
            "current_plan": self.current_plan,
            "step_codes": self.step_codes,
            "allow_yfinance": self.allow_yfinance
        }
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def load_from_file(cls, filename: str):
        """从文件加载计划和代码"""
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        planner = cls(allow_yfinance=data.get('allow_yfinance', False))
        planner.current_plan = data['current_plan']
        planner.step_codes = data['step_codes']
        return planner

    async def replay(self):
        from ..scheduler.replay_message_queue import ReplayMessageQueue
        async_queue = ReplayMessageQueue()
        if not self.current_plan or not self.step_codes:
            await async_queue.put({"type": "error", "content": "没有可重放的计划或代码。"})
            return

        self.reset()
        self.is_plan_confirmed = True

        for step in self.current_plan['steps']:
            self.current_step = step['step_number'] - 1
            await async_queue.put({"type": "message", "content": f"执行步骤 {step['step_number']}: {step['description']}"})

            if str(self.current_step) in self.step_codes:
                code = self.step_codes[str(self.current_step)]
                try:
                    result = self.execute_code(code)
                    if step['type'] == 'data_retrieval':
                        data = result['variables'][step['save_data_to']]
                        self.step_vars[step['save_data_to']] = data
                        await async_queue.put({"type": "code_execution", "content": f"数据已保存到 {step['save_data_to']}"})
                        
                        # 生成数据摘要
                        summary = self.data_summarizer.get_data_summary(data)
                        self.step_vars[f"{step['save_data_to']}_summary"] = summary
                        await async_queue.put({"type": "summary", "content": f"数据摘要: {summary}"})

                    elif step['type'] == 'data_analysis':
                        self.step_vars[f"analysis_result_{self.current_step}"] = result['variables']['analysis_result']
                        await async_queue.put({"type": "code_execution", "content": "分析结果已生成"})
                    
                    self.execution_results.append({"step": self.current_step, "type": step['type'], "result": result})
                except Exception as e:
                    await async_queue.put({"type": "error", "content": f"重放步骤 {step['step_number']} 时出错: {str(e)}"})
            else:
                await async_queue.put({"type": "error", "content": f"步骤 {step['step_number']} 没有对应的代码。"})

        await async_queue.put({"type": "message", "content": "所有步骤执行完成。正在生成最终报告..."})

        # 生成最终报告
        async for report_chunk in self.get_final_report():
            await async_queue.put(report_chunk)

        await async_queue.put({"type": "message", "content": "重放完成。"})