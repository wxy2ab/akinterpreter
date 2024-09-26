import functools
from typing import Callable, Any, Union, Iterator, List, Dict
import json

def handle_max_tokens(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        # 保存原始历史记录
        original_history = self.history.copy() if hasattr(self, 'history') else []
        
        def execute():
            nonlocal self, original_history
            try:
                # 尝试执行原始的 text_chat 方法
                return func(self, *args, **kwargs)
            except Exception as e:
                # 检查是否为最大 token 错误
                if "maximum context length" in str(e) or "maximum" in str(e) or "reduce the length" in str(e) or "最大" in str(e):
                    # 使用 one_chat 压缩历史记录
                    compressed_history = self.compress_history(original_history)
                    
                    # 更新实例的历史记录
                    self.history = compressed_history
                    
                    # 重新尝试执行 text_chat
                    return func(self, *args, **kwargs)
                else:
                    # 如果不是 token 限制错误，则重新抛出异常
                    raise e

        try:
            result = execute()
            if kwargs.get('is_stream', False):
                # 如果是流式模式，返回一个生成器
                def stream_wrapper():
                    if isinstance(result, Iterator):
                        yield from result
                    else:
                        yield result
                return stream_wrapper()
            else:
                # 如果不是流式模式，直接返回结果
                return result
        finally:
            # 清理原始历史记录
            if 'original_history' in locals():
                del original_history

    return wrapper