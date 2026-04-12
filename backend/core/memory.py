"""记忆系统模块"""

from datetime import datetime
from typing import Any, Optional

from .vector_memory import VectorMemory, HybridMemory, CHROMADB_AVAILABLE


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

    整合短期记忆和长期记忆，支持向量记忆。
    """

    def __init__(
        self,
        max_short_term: int = 100,
        enable_vector: bool = True,
        persist_dir: str = "./memory/chroma",
    ) -> None:
        """初始化记忆系统

        Args:
            max_short_term: 短期记忆最大条目数
            enable_vector: 是否启用向量记忆
            persist_dir: 向量记忆持久化目录
        """
        self.short_term = ShortTermMemory(max_items=max_short_term)
        self.long_term: dict[str, Any] = {}
        self.vector_memory: Optional[VectorMemory] = None
        self._enable_vector = enable_vector

        if enable_vector and CHROMADB_AVAILABLE:
            try:
                self.vector_memory = VectorMemory(persist_dir=persist_dir)
            except Exception:
                self.vector_memory = None

    def add(
        self,
        key: str,
        value: Any,
        memory_type: str = "short",
        requirement: Optional[str] = None,
        code: Optional[str] = None,
    ) -> None:
        """添加记忆

        Args:
            key: 键名
            value: 值
            memory_type: 记忆类型 (short/long/vector)
            requirement: 需求描述（用于向量记忆）
            code: 代码内容（用于向量记忆）
        """
        if memory_type == "short":
            self.short_term.add(key, value)
        elif memory_type == "long":
            self.long_term[key] = {
                "value": value,
                "timestamp": datetime.now().isoformat(),
            }
        elif memory_type == "vector" and self.vector_memory:
            if requirement and code:
                self.vector_memory.add(requirement, code, metadata={"key": key})

    def recall(self, query: str, k: int = 5) -> list[dict[str, Any]]:
        """回忆相关信息

        Args:
            query: 查询字符串
            k: 返回数量

        Returns:
            匹配的记忆列表
        """
        results = []

        # 从短期记忆搜索
        short_results = self.short_term.search(query, k)
        results.extend(short_results)

        # 从向量记忆搜索
        if self.vector_memory:
            vector_results = self.vector_memory.search(query, n_results=k)
            results.extend(vector_results)

        return results[:k]

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

    def clear_all(self) -> None:
        """清空所有记忆"""
        self.short_term.clear()
        self.long_term.clear()
        if self.vector_memory:
            self.vector_memory.clear()

    @property
    def is_vector_enabled(self) -> bool:
        """向量记忆是否启用"""
        return self.vector_memory is not None
