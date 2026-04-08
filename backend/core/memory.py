"""记忆系统模块"""

from datetime import datetime
from typing import Any, Optional


class ShortTermMemory:
    """短期记忆

    会话级别的记忆存储，有容量限制。
    """

    def __init__(self, max_items: int = 100) -> None:
        """初始化短期记忆

        Args:
            max_items: 最大条目数
        """
        self.items: list[dict[str, Any]] = []
        self.max_items = max_items

    def add(self, key: str, value: Any) -> None:
        """添加记忆

        Args:
            key: 键名
            value: 值
        """
        self.items.append(
            {
                "key": key,
                "value": value,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # 超过容量时移除最早的
        if len(self.items) > self.max_items:
            self.items.pop(0)

    def search(self, query: str, k: int = 5) -> list[dict[str, Any]]:
        """搜索记忆

        Args:
            query: 查询字符串
            k: 返回数量

        Returns:
            匹配的记忆列表
        """
        # 简单实现：返回最近的k条
        return self.items[-k:]

    def clear(self) -> None:
        """清空记忆"""
        self.items.clear()


class Memory:
    """记忆系统

    整合短期记忆和长期记忆。
    """

    def __init__(self, max_short_term: int = 100) -> None:
        """初始化记忆系统

        Args:
            max_short_term: 短期记忆最大条目数
        """
        self.short_term = ShortTermMemory(max_items=max_short_term)
        self.long_term: dict[str, Any] = {}

    def add(self, key: str, value: Any, memory_type: str = "short") -> None:
        """添加记忆

        Args:
            key: 键名
            value: 值
            memory_type: 记忆类型 (short/long)
        """
        if memory_type == "short":
            self.short_term.add(key, value)
        else:
            self.long_term[key] = {
                "value": value,
                "timestamp": datetime.now().isoformat(),
            }

    def recall(self, query: str, k: int = 5) -> list[dict[str, Any]]:
        """回忆相关信息

        Args:
            query: 查询字符串
            k: 返回数量

        Returns:
            匹配的记忆列表
        """
        short_results = self.short_term.search(query, k)
        return short_results

    def get_recent(self, n: int = 5) -> list[dict[str, Any]]:
        """获取最近的记忆

        Args:
            n: 返回数量

        Returns:
            最近的记忆列表
        """
        return self.short_term.items[-n:]

    def clear_short_term(self) -> None:
        """清空短期记忆"""
        self.short_term.clear()
