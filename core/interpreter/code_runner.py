import traceback
import tempfile
import os
import runpy
import subprocess
import io
import sys
from typing import Any, Dict, Tuple
import types

class CodeRunner:
    def __init__(self, debug=False):
        self.max_install_attempts = 5
        self.debug = debug

    def run(self, code: str, data: Any) -> Tuple[str, str]:
        old_stdout = sys.stdout
        redirected_output = io.StringIO()
        sys.stdout = redirected_output

        try:
            if self.debug:
                print("调试信息: 准备执行下面的代码:")
                print(code)
                print("\n调试信息: Data type:", type(data))
                print("\n调试信息: Data value:", repr(data))

            self.execute_with_dependency_handling(code, {'data': data})
            output = redirected_output.getvalue()
            error = None
        except Exception as e:
            output = redirected_output.getvalue()
            error = self.format_error(e, code)
        finally:
            sys.stdout = old_stdout

        return output, error

    def execute_with_dependency_handling(self, code: str, init_globals: Dict[str, Any]):
        import_error_count = 0
        while True:
            try:
                module = types.ModuleType("dynamic_module")
                module.__dict__.update(init_globals)
                module.__dict__['__name__'] = '__main__'
                
                exec(code, module.__dict__)
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

    def format_error(self, e: Exception, code: str) -> str:
        tb = traceback.extract_tb(sys.exc_info()[2])
        for i, frame in enumerate(tb):
            if frame.filename == "<string>":
                tb[i] = frame._replace(filename="<dynamic_code>")
        
        formatted_tb = traceback.format_list(tb)
        formatted_exception = traceback.format_exception_only(type(e), e)
        
        error_message = "Traceback (most recent call last):\n"
        error_message += "".join(formatted_tb)
        error_message += "".join(formatted_exception)
        
        if self.debug:
            error_message += "\n调试信息: Error occurred in the following code:\n"
            error_message += code
        
        return error_message
