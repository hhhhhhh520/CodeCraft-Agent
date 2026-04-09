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
        **kwargs: Any
    ) -> None:
        """初始化OpenAI LLM

        Args:
            model: 模型名称 (如 gpt-4, deepseek-chat)
            api_key: API密钥，如未提供则从环境变量读取
            base_url: API基础URL，用于兼容OpenAI格式的API（如DeepSeek）
            **kwargs: 额外配置参数
        """
        super().__init__(model, **kwargs)
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
        return response.choices[0].message.content or ""

    def stream(self, messages: list[dict[str, str]], **kwargs: Any) -> Iterator[str]:
        """流式调用OpenAI模型

        Args:
            messages: 消息列表
            **kwargs: 额外参数

        Yields:
            模型响应文本片段
        """
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
            **kwargs,
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
