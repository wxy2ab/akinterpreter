import subprocess
import sys
import io
import types
from typing import Any, Dict, Generator, Literal
import traceback

class SSECodeRunner:
    def __init__(self, debug=False):
        self.max_install_attempts = 5
        self.debug = debug

    def run_sse(self, code: str, global_vars: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        old_stdout = sys.stdout
        redirected_output = io.StringIO()
        sys.stdout = redirected_output

        try:
            if self.debug:
                yield {"type": "debug", "content": f"调试信息: 准备执行下面的代码:\n{code}"}

            updated_vars = self.execute_with_dependency_handling_sse(code, global_vars, redirected_output)
            
            # 返回更新后的变量
            yield {"type": "variables", "content": updated_vars}
            
            # 返回最后的输出
            final_output = redirected_output.getvalue()
            if final_output:
                yield {"type": "output", "content": final_output}

        except Exception as e:
            yield {"type": "output", "content": redirected_output.getvalue()}
            yield {"type": "error", "content": self.format_error(e, code)}
        finally:
            sys.stdout = old_stdout

    def execute_with_dependency_handling_sse(self, code: str, global_vars: Dict[str, Any], output_stream: io.StringIO) -> Dict[str, Any]:
        import pandas as pd
        import_error_count = 0
        while True:
            try:
                module = types.ModuleType("dynamic_module")
                module.__dict__.update(global_vars)
                module.__dict__['__name__'] = '__main__'
                module.__dict__['pd'] = pd

                def custom_print(*args, **kwargs):
                    print(*args, **kwargs, file=output_stream, flush=True)

                module.__dict__['print'] = custom_print

                exec(code, module.__dict__)

                # 更新并返回全局变量
                return {k: v for k, v in module.__dict__.items() 
                        if not k.startswith('__') and not isinstance(v, types.ModuleType)}

            except ImportError as e:
                import_error_count += 1
                if import_error_count > self.max_install_attempts:
                    raise Exception(f"遇到了太多导入错误（{import_error_count}次）。停止尝试。")
                if self.handle_import_error(str(e)):
                    continue
                else:
                    raise
            except Exception as e:
                raise Exception(f"执行代码时发生错误:\n{e}")

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