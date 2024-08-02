

from abc import ABC, abstractmethod
import ast
import json
from typing import Any, Dict, Generator, Set, Tuple, Type

from .llm_provider import LLMProvider

from ..planner.code_enhancement_system import CodeEnhancementSystem

from .llm_tools import LLMTools
from ..planner.message import send_message
from ._base_step_model import BaseStepModel
from .step_result import StepResult
from .step_data import StepData
from tenacity import retry,retry_if_exception,stop_after_attempt

class StepInfoGenerator(ABC):
    @property
    @abstractmethod
    def step_description(self) -> str:
        pass

    @property
    @abstractmethod
    def step_model(self) -> Type[BaseStepModel]:
        pass

    @property
    @abstractmethod
    def step_code_generator(self) -> Type["StepCodeGenerator"]:
        pass
    
    @property
    @abstractmethod
    def step_executor(self) -> Type["StepExecutor"]:
        pass

    @abstractmethod
    def get_step_model(self) -> BaseStepModel:
        pass

    @abstractmethod
    def gen_step_info(self, step_info :dict , query: str ) -> Generator[Dict[str, Any], None, BaseStepModel]:
        pass

    @abstractmethod
    def validate_step_info(self, step_info: dict) -> tuple[str, bool]:
        pass

    @abstractmethod
    def fix_step_info(self, step_data: BaseStepModel, query: str, error_msg: str) -> Generator[Dict[str, Any], None, None]:
        pass

class StepCodeGenerator(ABC):
    def __init__(self, step_info: BaseStepModel, step_data: StepData):
        self.step_info = step_info
        self.step_data = step_data
        self._step_code = ""
        self.llm_provider = LLMProvider()
        self.llm_tools = LLMTools()
        self.code_enhancement_system = CodeEnhancementSystem()
        self.llm_client = self.llm_provider.new_llm_client()
        
    @abstractmethod
    def gen_step_code(self) -> Generator[Dict[str, Any], None, None]:
        pass

    def fix_code(self, error: str) -> Generator[str, None, None]:
        if not self._step_code:
            yield send_message("没有可修复的代码。", "error")
            raise Exception("代码还没有生成，还无法修复.")

        retry_count = 0

        while True:
            try:
                retry_count = retry_count+1
                fix_prompt = self.fix_code_prompt(self._step_code, error)
                
                fixed_code = ""
                for chunk in self.llm_client.one_chat(fix_prompt, is_stream=True):
                    yield send_message(chunk, "code")
                    fixed_code += chunk
                
                self._step_code = self.llm_tools.extract_code(fixed_code)

                output,result = self.check_step_result(self._step_code)

                if not result:
                    error = output
                    yield send_message(output, "error")
                    raise Exception(output)
                yield send_message(f"代码已修复。")
                yield send_message(self._step_code, "code")
                break
            except Exception as e:
                if retry_count >= 3:
                    yield send_message("代码修复失败，无法继续执行。", "error")
                    raise Exception("代码修复失败")

    def pre_enhancement(self) -> Generator[str, None, None]:
        enhanced_prompt = self.code_enhancement_system.apply_pre_enhancement(
            self.step_info.type,
            self.step_info.description,
            "从akshare获取数据",
        )
        self.step_info.description = enhanced_prompt
        yield send_message("代码生成提示已增强", "info")
        yield send_message(enhanced_prompt, "enhanced_prompt")

    def post_enhancement(self) -> Generator[str, None, None]:
        # 第一步：检查代码是否有致命错误，要求返回 JSON 格式
        check_prompt = f"""
        请检查以下代码是否有影响运行的致命错误。如果有，请以 JSON 格式列出这些错误，格式如下：
        ```json
        [
            {{"error": "错误描述1", "line": "可能的问题行号1"}},
            {{"error": "错误描述2", "line": "可能的问题行号2"}}
        ]
        ```
        如果没有错误，请返回空列表：
        ```json
        []
        ```

        代码：
        ```python
        {self._step_code}
        ```
        """
        
        check_result = ""
        for chunk in self.llm_client.one_chat(check_prompt, is_stream=True):
            yield send_message(chunk, "code_check")
            check_result += chunk
        
        try:
            errors = self.llm_tools.extract_json_from_text(check_result)
        except json.JSONDecodeError:
            yield send_message("无法解析检查结果，将假定代码没有错误。", "warning")
            errors = []

        # 第二步：如果有致命错误，进行修复
        if errors:
            yield send_message(f"检测到代码中存在 {len(errors)} 个潜在问题，正在进行修复...", "info")
            
            error_descriptions = "\n".join([f"- {error['error']} (可能在第 {error['line']} 行)" for error in errors])
            fix_prompt = f"""
            以下代码存在一些问题：
            ```python
            {self._step_code}
            ```

            这些问题包括：
            {error_descriptions}

            请修复这些问题，并提供完整的修正后的代码。修复后的代码使用 ```python 和 ``` 包裹。
            """
            
            fixed_code = ""
            for chunk in self.llm_client.text_chat(fix_prompt, is_stream=True):
                yield send_message(chunk, "code_fix")
                fixed_code += chunk
            
            self._step_code = self.llm_tools.extract_code(fixed_code)
            yield send_message("代码已修复完成。", "info")
            yield send_message(self._step_code, "full_code")
        else:
            yield send_message("代码检查完成，未发现致命错误。", "info")

    @staticmethod
    def fix_code_prompt(code: str, error: str) -> str:
        return f"""
        以下代码导致了一个错误：
        ```python
        {code}
        ```

        错误信息：
        {error}

        请修复代码以解决此错误。提供完整的修正后的代码。
        修复后的代码使用 ```python 和 ``` 包裹。
        """

    @property
    @abstractmethod
    def step_code(self) -> str:
        pass

    @abstractmethod
    def make_step_sure(self):
        pass

    def check_step_result(self, code: str) -> Tuple[str, bool]:
        tree = ast.parse(code)
        required_vars = set(self.step_info.save_data_to)
        if hasattr(self.step_info, "analysis_result"):
            required_vars.add(self.step_info.analysis_result)
        
        assigned_vars = self.get_assigned_variables(tree)
        
        # 检查是否正确导入 code_tools
        if not self.check_code_tools_import(tree):
            return "缺少正确的 code_tools 导入语句。应该有：from core.utils.code_tools import code_tools", False
        
        # 检查是否正确使用 code_tools.add()
        missing_vars = self.check_code_tools_usage(tree, required_vars)
        
        if missing_vars:
            return f"以下变量未使用 code_tools.add() 正确保存: {', '.join(missing_vars)}", False
        
        return "", True

    def get_assigned_variables(self, tree: ast.AST) -> Set[str]:
        assigned_vars = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        assigned_vars.add(target.id)
            elif isinstance(node, ast.AugAssign):
                if isinstance(target, ast.Name):
                    assigned_vars.add(node.target.id)
        return assigned_vars

    def check_code_tools_import(self, tree: ast.AST) -> bool:
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module == 'core.utils.code_tools' and any(alias.name == 'code_tools' for alias in node.names):
                    return True
        return False

    def check_code_tools_usage(self, tree: ast.AST, required_vars: Set[str]) -> Set[str]:
        missing_vars = set(required_vars)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr == 'add' and isinstance(node.func.value, ast.Name) and node.func.value.id == 'code_tools':
                        if len(node.args) >= 2 and isinstance(node.args[0], ast.Str):
                            var_name = node.args[0].s
                            if var_name in missing_vars:
                                missing_vars.remove(var_name)
        return missing_vars

class StepExecutor(ABC):
    def __init__(self,step_info:BaseStepModel ,step_data:StepData):
        self.step_data = step_data
        self.step_info = step_info
        self.llm_provider = LLMProvider()
        self.llm_tools = LLMTools()
        self.code_runner = self.llm_provider.new_code_runner()
        self.llm_client  = self.llm_provider.new_llm_client()
        self.max_retry = 8

    @retry(stop=stop_after_attempt(3))
    def execute_step_code(self) -> Generator[Dict[str, Any], None, None]:
        step_number = self.step_info.step_number
        code = self.step_data.get_step_code(step_number)
        is_code_changed = False
        count = 0
        while True:
            try:
                count += 1
                yield from self.code_runner.run_sse(code, self.step_data.global_vars)
                output,result = self.check_step_result()
                if not result:
                    yield send_message(output, "error")
                    raise Exception(output)
                if is_code_changed:
                    self.step_data.set_step_code(step_number, code)
                break
            except Exception as e:
                is_code_changed = True
                yield send_message(f"代码执行失败：{str(e)}", "error")
                generator = self.fix_code(code, str(e))
                for chunk in generator:
                    if chunk["type"] == "full_code":
                        code = chunk["content"]
                    yield chunk
                if count >=2:
                    yield send_message("代码修复失败，无法继续执行。", "error")
                    raise e
        yield send_message("代码执行完成", "message")
    
    def fix_code(self, code:str, error: str) -> Generator[str, None, None]:
        fix_prompt = self.fix_code_prompt(code, error)
        
        fixed_code = ""
        for chunk in self.llm_client.one_chat(fix_prompt, is_stream=True):
            yield send_message(chunk, "code")
            fixed_code += chunk
        
        step_code = self.llm_tools.extract_code(fixed_code)
        yield send_message(f"代码已修复。")
        yield send_message(step_code, "full_code")

    def redo_step(self) -> Generator[Dict[str, Any], None, None]:
        step_number = self.step_info.step_number
        code = self.step_data.get_step_code(step_number)
        yield from self.code_runner.run_sse(code, self.step_data.global_vars)

    def check_step_result(self)-> tuple[str, bool]:
        if hasattr(self.step_data, "analysis_result"):
            analysis_result =  self.step_info.analysis_result
            if not self.step_data.is_exists(analysis_result):
                return f"分析结果不存在,需要把分析结果存储于{analysis_result}", False
        save_data_to = self.step_info.save_data_to
        for data_var in save_data_to:
            if not self.step_data.is_exists(data_var):
                return f"数据 {data_var} 不存在,需要把数据存储于{data_var}", False
        return "", True

    @staticmethod
    def fix_code_prompt(code: str, error: str) -> str:
        return f"""
        以下代码导致了一个错误：
        ```python
        {code}
        ```

        错误信息：
        {error}

        请修复代码以解决此错误。提供完整的修正后的代码。
        修复后的代码使用 ```python 和 ``` 包裹。
        """

class StepReport(ABC):
    @abstractmethod
    def gen_report(self) -> Generator[Dict[str, Any], None, None]:
        pass
