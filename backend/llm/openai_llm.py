"""OpenAI LLM实现模块"""

from typing import Any, Iterator, Optional

from openai import OpenAI

from .base import BaseLLM


class OpenAILLM(BaseLLM):
    """OpenAI LLM实现

    封装OpenAI API调用，支持OpenAI兼容的API（如DeepSeek）。
    """

    def __init__(
        self,
        model: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        token_manager: Optional[Any] = None,
        **kwargs: Any
    ) -> None:
        """初始化OpenAI LLM

        Args:
            model: 模型名称 (如 gpt-4, deepseek-chat)
            api_key: API密钥，如未提供则从环境变量读取
            base_url: API基础URL，用于兼容OpenAI格式的API（如DeepSeek）
            token_manager: Token管理器实例
            **kwargs: 额外配置参数
        """
        super().__init__(model, token_manager=token_manager, **kwargs)
        self.api_key = api_key
        self.base_url = base_url
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def invoke(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        """调用OpenAI模型

        Args:
            messages: 消息列表
            **kwargs: 额外参数 (temperature, max_tokens等)

        Returns:
            模型响应文本
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            **kwargs,
        )
        content = response.choices[0].message.content or ""

        # 追踪Token使用量
        self._track_tokens(content)

        # 如果API返回了token使用量，使用实际值
        if hasattr(response, 'usage') and response.usage and self.token_manager:
            actual_tokens = response.usage.total_tokens
            # 重置之前的估算，使用实际值
            self.token_manager.current_usage -= self.token_manager.estimate_tokens(content)
            self.token_manager.track_usage(actual_tokens)

        return content

    def stream(self, messages: list[dict[str, str]], **kwargs: Any) -> Iterator[str]:
        """流式调用OpenAI模型

        Args:
            messages: 消息列表
            **kwargs: 额外参数

        Yields:
            模型响应文本片段
        """
        full_content = ""
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
            **kwargs,
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_content += content
                yield content

        # 流式结束后追踪总Token
        self._track_tokens(full_content)
