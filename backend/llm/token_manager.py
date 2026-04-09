"""Token管理器模块"""

from typing import Any


class TokenManager:
    """Token管理器

    管理和追踪Token使用量。
    """

    def __init__(self, max_tokens: int = 128000) -> None:
        """初始化Token管理器

        Args:
            max_tokens: 最大Token数
        """
        self.max_tokens = max_tokens
        self.current_usage = 0

    def estimate_tokens(self, text: str) -> int:
        """估算文本Token数

        简单估算：中文约1.5字符/token，英文约4字符/token

        Args:
            text: 文本字符串

        Returns:
            估算的Token数
        """
        # 简单估算
        return max(1, len(text) // 3)

    def should_compress(self, context: str) -> bool:
        """判断是否需要压缩上下文

        Args:
            context: 上下文文本

        Returns:
            是否需要压缩
        """
        estimated = self.estimate_tokens(context)
        threshold = self.max_tokens * 0.8
        return estimated > threshold

    def track_usage(self, usage: int) -> None:
        """追踪Token使用量

        Args:
            usage: 使用的Token数
        """
        self.current_usage += usage

    def reset(self) -> None:
        """重置使用量"""
        self.current_usage = 0

    def get_remaining(self) -> int:
        """获取剩余可用Token数

        Returns:
            剩余Token数
        """
        return max(0, self.max_tokens - self.current_usage)
