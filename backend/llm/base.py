"""LLM抽象基类模块"""

from abc import ABC, abstractmethod
from typing import Any, Iterator


class BaseLLM(ABC):
    """LLM抽象基类

    定义所有LLM实现必须遵循的接口。
    """

    def __init__(self, model: str, **kwargs: Any) -> None:
        """初始化LLM

        Args:
            model: 模型名称
            **kwargs: 额外配置参数
        """
        self.model = model
        self.config = kwargs

    @abstractmethod
    def invoke(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        """调用模型

        Args:
            messages: 消息列表
            **kwargs: 额外参数

        Returns:
            模型响应文本
        """
        pass

    @abstractmethod
    def stream(self, messages: list[dict[str, str]], **kwargs: Any) -> Iterator[str]:
        """流式调用模型

        Args:
            messages: 消息列表
            **kwargs: 额外参数

        Yields:
            模型响应文本片段
        """
        pass


class LLMFactory:
    """LLM工厂类

    用于创建不同provider的LLM实例。
    """

    @staticmethod
    def create(provider: str, model: str, **kwargs: Any) -> BaseLLM:
        """创建LLM实例

        Args:
            provider: 提供商名称 (openai, claude)
            model: 模型名称
            **kwargs: 额外配置参数

        Returns:
            LLM实例

        Raises:
            ValueError: 未知的provider
        """
        if provider == "openai":
            from .openai_llm import OpenAILLM

            return OpenAILLM(model, **kwargs)
        elif provider == "claude":
            from .claude_llm import ClaudeLLM

            return ClaudeLLM(model, **kwargs)
        else:
            raise ValueError(f"Unknown provider: {provider}")
