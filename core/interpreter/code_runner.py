import traceback
import tempfile
import os
import runpy
import subprocess
import io
import sys
from typing import Any, Dict, Literal, Tuple
import types

class CodeRunner:
    def __init__(self, debug=False):
        self.max_install_attempts = 5
        self.debug = debug

    def run(self, code: str, data: Any) -> Tuple[str, str]:
        old_stdout = sys.stdout
        redirected_output = io.StringIO()
        sys.stdout = redirected_output
        init_globals=None
        if isinstance(data, dict):
            init_globals = data
        else:
            init_globals = {'data': data}
        
        try:
            if self.debug:
                print("调试信息: 准备执行下面的代码:")
                print(code)
                print("\n调试信息: Data type:", type(data))
                print("\n调试信息: Data value:", repr(data))

            self.execute_with_dependency_handling(code,init_globals)
            output = redirected_output.getvalue()
            error = None
        except Exception as e:
            output = redirected_output.getvalue()
            error = self.format_error(e, code)
        finally:
            sys.stdout = old_stdout

        return output, error

    def execute_with_dependency_handling(self, code: str, init_globals: Dict[str, Any]):
        import pandas as pd
        import_error_count = 0
        while True:
            try:
                init_globals["pd"]=pd
                module = types.ModuleType("dynamic_module")
                module.__dict__.update(init_globals)
                module.__dict__['__name__'] = '__main__'
                
                exec(code, module.__dict__)
                
                # 执行成功后，更新 init_globals
                for key, value in module.__dict__.items():
                    # 只更新非内置和非模块的变量
                    if not key.startswith('__') and not isinstance(value, types.ModuleType):
                        init_globals[key] = value
                
                break  # 如果执行成功，跳出循环
            except ImportError as e:
                import_error_count += 1
                if import_error_count > self.max_install_attempts:
                    print(f"遇到了太多导入错误（{import_error_count}次）。停止尝试。")
                    raise
                if self.handle_import_error(str(e)):
                    continue  # 如果成功处理了导入错误，重新尝试执行代码
                else:
                    raise  # 如果无法处理导入错误，抛出异常
            except Exception as e:
                print(f"执行代码时发生错误:\n{e}")
                raise

        return init_globals

    def handle_import_error(self, error_message: str) -> bool:
        module_name = error_message.split("'")[1] if "'" in error_message else ""
        if not module_name:
            return False

        print(f"尝试安装模块: {module_name}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", module_name])
            print(f"成功安装模块: {module_name}")
            return True
        except subprocess.CalledProcessError:
            print(f"无法安装模块: {module_name}")
            return False

    def format_error(self, e: Exception, code: str, info_level: Literal["short", "medium", "long", "all"] = "all") -> str:
        tb = traceback.extract_tb(sys.exc_info()[2])

        # 替换 <string> 为 <dynamic_code>
        for i, frame in enumerate(tb):
            if frame.filename == "<string>":
                tb[i] = traceback.FrameSummary(
                    filename="<dynamic_code>",
                    lineno=frame.lineno,
                    name=frame.name,
                    line=frame.line
                )

        error_message = ""

        if info_level in ["medium", "long", "all"]:
            formatted_tb = traceback.format_list(tb)
            error_message += "Traceback (most recent call last):\n"
            error_message += "".join(formatted_tb)

        if info_level in ["long", "all"]:
            formatted_exception = traceback.format_exception_only(type(e), e)
            error_message += "".join(formatted_exception)

        if info_level == "all" and self.debug:
            error_message += "\n调试信息: Error occurred in the following code:\n"
            error_message += code

        elif info_level == "short":
            error_message = f"Error: {type(e).__name__}: {e}"
        
        return error_message

    def _execute_code_with_vars(self, code: str, global_vars: Dict[str, Any]) -> Tuple[str, str]:
        # 创建一个临时文件
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.py', delete=False) as temp_file:
            # 直接写入要执行的代码
            temp_file.write(code)
            temp_file.flush()
            temp_file_path = temp_file.name

        # 保存原始的 stdout
        old_stdout = sys.stdout
        redirected_output = io.StringIO()
        sys.stdout = redirected_output

        output = None
        error = None

        try:
            # 使用 runpy 执行代码
            namespace = runpy.run_path(temp_file_path, global_vars)
            
            # 更新全局变量和局部变量，包括新创建的变量
            global_vars.update({k: v for k, v in namespace.items() })
            
            output = redirected_output.getvalue()
        except Exception as e:
            error = traceback.format_exc()
        finally:
            sys.stdout = old_stdout
            # 删除临时文件
            os.unlink(temp_file_path)

        return output, error