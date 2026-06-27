"""Claude LLM实现模块"""

import logging
from typing import Any, Iterator, Optional

from anthropic import Anthropic, RateLimitError, APITimeoutError, APIConnectionError, APIStatusError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .base import BaseLLM

logger = logging.getLogger("codecraft.llm.claude")


class ClaudeLLM(BaseLLM):
    """Claude LLM实现

    封装Anthropic API调用。
    """

    def __init__(
        self, model: str, api_key: Optional[str] = None, token_manager: Optional[Any] = None,
        timeout: float = 30.0, max_retries: int = 3, **kwargs: Any
    ) -> None:
        """初始化Claude LLM

        Args:
            model: 模型名称 (如 claude-3-5-sonnet-20241022)
            api_key: API密钥，如未提供则从环境变量读取
            token_manager: Token管理器实例
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
            **kwargs: 额外配置参数
        """
        super().__init__(model, token_manager=token_manager, **kwargs)
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.client = Anthropic(api_key=api_key, timeout=timeout, max_retries=0)

    @retry(
        retry=retry_if_exception_type((RateLimitError, APITimeoutError, APIConnectionError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        before_sleep=lambda retry_state: logger.warning(
            f"LLM调用失败，正在重试 ({retry_state.attempt_number}/3): {retry_state.outcome.exception()}"
        ) if retry_state.outcome else None,
    )
    def invoke(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        """调用Claude模型

        Args:
            messages: 消息列表
            **kwargs: 额外参数 (temperature, max_tokens等)

        Returns:
            模型响应文本
        """
        # 转换消息格式
        system_message = ""
        claude_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                claude_messages.append(
                    {"role": msg["role"], "content": msg["content"]}
                )

        response = self.client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 4096),
            system=system_message if system_message else None,
            messages=claude_messages,
        )

        content = response.content[0].text

        # 追踪Token使用量
        self._track_tokens(content)

        # 如果API返回了token使用量，使用实际值
        if hasattr(response, 'usage') and response.usage and self.token_manager:
            actual_tokens = response.usage.input_tokens + response.usage.output_tokens
            self.token_manager.current_usage -= self.token_manager.estimate_tokens(content)
            self.token_manager.track_usage(actual_tokens)

        return content

    def stream(self, messages: list[dict[str, str]], **kwargs: Any) -> Iterator[str]:
        """流式调用Claude模型

        Args:
            messages: 消息列表
            **kwargs: 额外参数

        Yields:
            模型响应文本片段
        """
        system_message = ""
        claude_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                claude_messages.append(
                    {"role": msg["role"], "content": msg["content"]}
                )

        full_content = ""
        with self.client.messages.stream(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 4096),
            system=system_message if system_message else None,
            messages=claude_messages,
        ) as stream:
            for text in stream.text_stream:
                full_content += text
                yield text

        # 流式结束后追踪总Token
        self._track_tokens(full_content)
