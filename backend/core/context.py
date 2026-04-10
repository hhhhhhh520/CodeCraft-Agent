"""共享上下文模块"""

import threading
import uuid
from typing import Any, Optional


class SharedContext:
    """共享上下文

    在多Agent协作过程中共享数据。
    使用RLock确保线程安全。
    """

    def __init__(self) -> None:
        """初始化共享上下文"""
        self.task_id: str = str(uuid.uuid4())
        self.data: dict[str, Any] = {}
        self._lock = threading.RLock()  # 可重入锁，确保线程安全

    def set(self, key: str, value: Any) -> None:
        """设置数据

        Args:
            key: 键名
            value: 值
        """
        with self._lock:
            self.data[key] = value

    def get(self, key: str, default: Optional[Any] = None) -> Optional[Any]:
        """获取数据

        Args:
            key: 键名
            default: 默认值

        Returns:
            对应的值，如不存在则返回默认值
        """
        with self._lock:
            return self.data.get(key, default)

    def update(self, data: dict[str, Any]) -> None:
        """批量更新数据

        Args:
            data: 要更新的数据字典
        """
        with self._lock:
            self.data.update(data)

    def clear(self) -> None:
        """清空上下文"""
        with self._lock:
            self.data.clear()

    def to_dict(self) -> dict[str, Any]:
        """转换为字典

        Returns:
            包含所有数据的字典
        """
        with self._lock:
            return {"task_id": self.task_id, "data": self.data.copy()}

    def keys(self) -> list[str]:
        """获取所有键名

        Returns:
            键名列表
        """
        with self._lock:
            return list(self.data.keys())

    def __contains__(self, key: str) -> bool:
        """检查键是否存在"""
        with self._lock:
            return key in self.data

    def __len__(self) -> int:
        """返回数据项数量"""
        with self._lock:
            return len(self.data)
