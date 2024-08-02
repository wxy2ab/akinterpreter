import ast
import sys
import io
import os
from typing import Any, Dict, Generator, Tuple

class ASTCodeRunner:
    def __init__(self, debug=False):
        self.debug = debug

    def run_sse(self, code: str, global_vars: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        old_stdout = sys.stdout
        redirected_output = io.StringIO()
        sys.stdout = redirected_output

        try:
            if self.debug:
                yield {"type": "debug", "content": f"调试信息: 准备执行下面的代码:\n{code}"}

            tree = ast.parse(code)
            self.check_security(tree)  # 添加安全检查

            exec_globals = global_vars.copy()
            exec_globals['print'] = lambda *args, **kwargs: print(*args, **kwargs, file=redirected_output, flush=True)
            exec_globals['open'] = self.safe_open  # 使用安全的 open 函数

            # 使用 exec 执行整个代码块，而不是逐节点执行
            exec(compile(tree, '<string>', 'exec'), exec_globals)

            # 捕获输出
            output = redirected_output.getvalue()
            if output:
                yield {"type": "message", "content": output}

            # 返回更新后的变量
            updated_vars = {k: v for k, v in exec_globals.items() if k not in global_vars or global_vars[k] is not v}
            yield {"type": "message", "content": updated_vars}

        except Exception as e:
            yield {"type": "error", "content": str(e)}
            raise e
        finally:
            sys.stdout = old_stdout

    def run(self, code: str, global_vars: Dict[str, Any]={}) -> Dict[str, Any]:
        """
        input:
            code: 代码字符串
            global_vars: 全局变量字典
        output:
            result: 执行结果字典
                output: 标准输出
                error: 错误信息
                updated_vars: 更新后的全局变量
                debug: 调试信息
        """
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
                result["debug"] = f"调试信息: 准备执行下面的代码:\n{code}"

            # 准备执行环境
            exec_globals = global_vars.copy()
            
            # 执行代码
            exec(code, exec_globals)

            # 捕获输出
            result["output"] = redirected_output.getvalue()

            # 返回更新后的变量
            result["updated_vars"] = {k: v for k, v in exec_globals.items() if k not in global_vars or global_vars[k] is not v}

        except Exception as e:
            result["error"] = f"{type(e).__name__}: {str(e)}"
            result["error"] += f"\n{redirected_error.getvalue()}"
        finally:
            # 恢复标准输出和错误流
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        return result

    def execute_node(self, node, exec_globals):
        if isinstance(node, ast.Expr):
            # 表达式语句
            eval(compile(ast.Expression(node.value), '<string>', 'eval'), exec_globals)
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
            # 函数和类定义
            exec(compile(ast.Module([node], type_ignores=[]), '<string>', 'exec'), exec_globals)
        elif isinstance(node, ast.Import):
            # 导入语句
            for alias in node.names:
                exec(f"import {alias.name}", exec_globals)
        elif isinstance(node, ast.ImportFrom):
            # from ... import 语句
            exec(compile(ast.Module([node], type_ignores=[]), '<string>', 'exec'), exec_globals)
        else:
            # 其他类型的语句
            exec(compile(ast.Module([node], type_ignores=[]), '<string>', 'exec'), exec_globals)

    def check_security(self, tree):
        for node in ast.walk(tree):
            # 检查是否有删除文件的操作
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == 'remove' and isinstance(node.func.value, ast.Name) and node.func.value.id == 'os':
                    raise SecurityException("禁止删除文件")
                
            # 检查是否有重命名文件的操作（可能被用来删除文件）
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == 'rename' and isinstance(node.func.value, ast.Name) and node.func.value.id == 'os':
                    raise SecurityException("禁止重命名文件")

    def safe_open(self, file, mode='r', buffering=-1, encoding=None, errors=None, newline=None, closefd=True, opener=None):
        # 检查文件路径是否在允许的范围内
        abs_path = os.path.abspath(file)
        if not abs_path.startswith(os.path.abspath('.')):
            raise SecurityException(f"禁止访问 ./ 目录以外的文件: {file}")
        
        # 禁止写入和追加模式
        if 'w' in mode or 'a' in mode or '+' in mode:
            raise SecurityException(f"禁止写入或修改文件: {file}")
        
        return open(file, mode, buffering, encoding, errors, newline, closefd, opener)

class SecurityException(Exception):
    pass