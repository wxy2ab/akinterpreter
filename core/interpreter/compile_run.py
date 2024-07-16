import sys
import io
from typing import Dict, Any

class CompileExecRunner:
    def __init__(self, debug=False):
        self.debug = debug

    def compile_run(self, code: str, global_vars: Dict[str, Any] = None) -> Dict[str, Any]:
        # 准备捕获输出
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        redirected_output = io.StringIO()
        redirected_error = io.StringIO()
        sys.stdout = redirected_output
        sys.stderr = redirected_error

        result = {
            "output": "",
            "error": None,
            "updated_vars": {},
            "debug": None
        }

        try:
            if self.debug:
                result["debug"] = f"调试信息: 准备编译并执行以下代码:\n{code}"

            # 准备执行环境
            exec_globals = global_vars.copy() if global_vars else {}
            
            # 编译代码
            compiled_code = compile(code, '<string>', 'exec')
            
            # 执行编译后的代码
            exec(compiled_code, exec_globals)

            # 捕获输出
            result["output"] = redirected_output.getvalue()

            # 返回更新后的变量
            if global_vars:
                result["updated_vars"] = {k: v for k, v in exec_globals.items() if k not in global_vars or global_vars[k] is not v}
            else:
                result["updated_vars"] = exec_globals

        except Exception as e:
            result["error"] = f"{type(e).__name__}: {str(e)}"
            result["error"] += f"\n{redirected_error.getvalue()}"
        finally:
            # 恢复标准输出和错误流
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        return result

# 使用示例
if __name__ == "__main__":
    runner = CompileExecRunner(debug=True)
    code = '''
import akshare as ak

cailian_api_news = ak.stock_news_em(symbol="300059")
print(cailian_api_news.head())
'''
    global_vars = {}
    result = runner.compile_run(code, global_vars)
    print("Execution Result:")
    print(f"Output: {result['output']}")
    print(f"Error: {result['error']}")
    print(f"Updated Variables: {result['updated_vars']}")
    print(f"Debug Info: {result['debug']}")