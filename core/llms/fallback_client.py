
from typing import Union, List, Dict, Any, Iterator
from ._llm_api_client import LLMApiClient
from ..utils.config_setting import Config
import random
import re
from collections import defaultdict
from core.utils.log import logger
from traceback import format_exc
import traceback

class LoadBalancer:
    """负载均衡器，用于在多个 LLM 实例之间分配请求"""
    
    def __init__(self, llms: List[Any], weights: List[float] = None):
        """
        初始化负载均衡器
        
        Args:
            llms: LLM实例列表
            weights: 权重列表，如果不提供则平均分配
        """
        self.llms = llms
        if weights is None:
            # 平均分配权重
            self._weights = [1.0 / len(llms)] * len(llms)
        else:
            # 确保权重和为1
            total = sum(weights)
            self._weights = [w / total for w in weights]
            
        # 初始化计数器
        self.request_counts = defaultdict(int)
    
    def get_next_llm(self) -> Any:
        """基于权重随机选择下一个LLM实例"""
        chosen_llm = random.choices(self.llms, weights=self._weights, k=1)[0]
        self.request_counts[id(chosen_llm)] += 1
        return chosen_llm
    
    def get_stats(self) -> Dict[str, int]:
        """获取每个LLM的请求统计"""
        return {
            f"LLM_{i}": self.request_counts[id(llm)] 
            for i, llm in enumerate(self.llms)
        }

class FallbackLLMClient(LLMApiClient):
    def __init__(self):
        config = Config()
        self.main_llm_config = config.get("MAIN_LLM", "FallbackLLMClient") or "QianWenClient"
        self.auxiliary_llms = config.get("AUXILIARY_LLMS", "FallbackLLMClient") or "MiniMaxProClient,GLMFreeClient,SimpleDeepSeekClient"
        # 获取权重配置
        self.weights_config = config.get("MAIN_LLM_WEIGHTS", "FallbackLLMClient") or None
        self.llm_factory = None
        self.main_balancer = None  # 主LLM负载均衡器
        self.auxiliary_llms_list = None  # 备用LLM列表
        self.logger = logger

        # 输出完整的调用堆栈
        print("=" * 80)
        print("调用堆栈跟踪:")
        print("=" * 80)
        traceback.print_stack()
        print("=" * 80)
        
        
    def _parse_llm_config(self, config_str: str) -> List[str]:
        """解析LLM配置字符串，返回LLM名称列表"""
        return [name.strip() for name in config_str.split(',')]

    def _parse_weights(self, weights_str: str, num_llms: int) -> List[float]:
        """
        解析权重配置字符串
        如果格式无效或未提供，返回None（表示使用平均分配）
        """
        if not weights_str:
            return None
            
        try:
            weights = [float(w.strip()) for w in weights_str.split(',')]
            if len(weights) != num_llms:
                self.logger.warning(
                    f"Weights count ({len(weights)}) doesn't match LLM count ({num_llms}). "
                    "Using equal distribution."
                )
                return None
            return weights
        except ValueError:
            self.logger.warning("Invalid weight format. Using equal distribution.")
            return None

    def _lazy_init(self):
        """延迟初始化LLM实例和负载均衡器"""
        if self.main_balancer is None:
            from .llm_factory import LLMFactory
            self.llm_factory = LLMFactory()
            
            # 初始化主LLM实例
            main_llm_names = self._parse_llm_config(self.main_llm_config)
            main_llms = [self.llm_factory.get_instance(name) for name in main_llm_names]
            
            # 解析权重并创建负载均衡器
            weights = self._parse_weights(self.weights_config, len(main_llms))
            self.main_balancer = LoadBalancer(main_llms, weights)
            
            # 初始化备用LLM实例
            auxiliary_llm_names = self._parse_llm_config(self.auxiliary_llms)
            if auxiliary_llm_names:  # 如果备用LLM配置非空
                self.auxiliary_llms_list = [
                    self.llm_factory.get_instance(name) 
                    for name in auxiliary_llm_names
                ]
            else:
                self.logger.warning("No auxiliary LLMs configured. Skipping auxiliary LLMs initialization.")
                self.auxiliary_llms_list = []  # 如果没有配置备用LLM，设置为空列表

    def _execute_with_fallback(self, method_name: str, *args, **kwargs):
        """使用负载均衡和故障转移执行LLM方法"""
        self._lazy_init()
        
        # 首先尝试使用负载均衡的主LLM
        try:
            main_llm = self.main_balancer.get_next_llm()
            method = getattr(main_llm, method_name)
            return method(*args, **kwargs)
        except Exception as main_error:
            self.logger.warning(f"Main LLM failed: {str(main_error)}")
            if self.auxiliary_llms_list is None:
                auxiliary_llm_names = self._parse_llm_config(self.auxiliary_llms)
                self.auxiliary_llms_list = [
                    self.llm_factory.get_instance(name) 
                    for name in auxiliary_llm_names
                ]
            # 如果主LLM失败，依次尝试备用LLM
            for aux_llm in self.auxiliary_llms_list:
                try:
                    method = getattr(aux_llm, method_name)
                    return method(*args, **kwargs)
                except Exception as e:
                    self.logger.warning(f"{type(aux_llm).__name__} failed: {str(e)} {format_exc()}")
            
            # 如果所有LLM都失败，抛出异常
            raise Exception("All LLMs failed")

    def one_chat(self, message: Union[str, List[Union[str, Any]]], is_stream: bool = False) -> Union[str, Iterator[str]]:
        return self._execute_with_fallback("one_chat", message, is_stream)

    def text_chat(self, message: str, is_stream: bool = False) -> Union[str, Iterator[str]]:
        return self._execute_with_fallback("text_chat", message, is_stream)

    def tool_chat(self, user_message: str, tools: List[Dict[str, Any]], function_module: Any, is_stream: bool = False) -> Union[str, Iterator[str]]:
        return self._execute_with_fallback("tool_chat", user_message, tools, function_module, is_stream)

    def tool_invoke(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        return self._execute_with_fallback("tool_invoke", messages, tools)

    def audio_chat(self, message: str, audio_path: str) -> str:
        return self._execute_with_fallback("audio_chat", message, audio_path)

    def video_chat(self, message: str, video_path: str) -> str:
        return self._execute_with_fallback("video_chat", message, video_path)

    def clear_chat(self):
        """清除所有LLM的聊天历史"""
        self._lazy_init()
        for llm in self.main_balancer.llms:
            llm.clear_chat()
        for llm in self.auxiliary_llms_list:
            llm.clear_chat()

    def get_stats(self) -> Dict[str, Any]:
        """获取所有LLM的统计信息"""
        self._lazy_init()
        stats = {
            "main_llms": self.main_balancer.get_stats(),
            "auxiliary_llms": {}
        }
        for i, llm in enumerate(self.auxiliary_llms_list):
            stats["auxiliary_llms"][f"AUX_LLM_{i}"] = llm.get_stats()
        return stats
