"""向量记忆系统模块

基于ChromaDB的向量记忆系统，支持语义检索历史代码。

安全注意事项：
- 向量数据库存储在本地文件系统
- 包含用户需求描述和生成的代码
- 建议在生产环境中使用加密存储或限制访问权限
"""

import os
import stat
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False


def _set_secure_permissions(path: str) -> None:
    """设置安全目录权限（仅所有者可访问）

    Args:
        path: 目录路径
    """
    if os.name == 'posix':
        os.chmod(path, stat.S_IRWXU)  # 700: 仅所有者读写执行


class VectorMemory:
    """基于ChromaDB的向量记忆系统

    提供代码片段的向量化存储和语义检索功能。

    安全说明：
    - 数据以明文存储在本地文件系统
    - 目录权限设置为仅所有者可访问（POSIX系统）
    - 不应存储敏感信息（如API Key、密码等）
    """

    # 敏感信息关键词（不应存储）
    SENSITIVE_KEYWORDS = [
        "api_key", "apikey", "password", "secret", "token",
        "credential", "private_key", "access_key",
    ]

    def __init__(
        self,
        persist_dir: str = "./memory/chroma",
        collection_name: str = "code_memory",
    ) -> None:
        """初始化向量记忆系统

        Args:
            persist_dir: 持久化目录
            collection_name: 集合名称
        """
        if not CHROMADB_AVAILABLE:
            raise ImportError(
                "ChromaDB未安装，请运行: pip install chromadb"
            )

        # 确保目录存在并设置安全权限
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        _set_secure_permissions(persist_dir)

        # 初始化ChromaDB客户端
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.persist_dir = persist_dir

        # 获取或创建集合
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Code generation history"},
        )

        self._doc_counter = 0

    def _check_sensitive_content(self, text: str) -> bool:
        """检查文本是否包含敏感信息

        Args:
            text: 要检查的文本

        Returns:
            是否包含敏感信息
        """
        text_lower = text.lower()
        for keyword in self.SENSITIVE_KEYWORDS:
            if keyword in text_lower:
                return True
        return False

    def add(
        self,
        requirement: str,
        code: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        """添加代码记忆

        Args:
            requirement: 需求描述
            code: 生成的代码
            metadata: 额外元数据

        Returns:
            文档ID

        Raises:
            ValueError: 如果内容包含敏感信息
        """
        # 安全检查：不应存储敏感信息
        if self._check_sensitive_content(requirement):
            raise ValueError("需求描述包含敏感信息，不应存储到向量记忆")
        if self._check_sensitive_content(code):
            raise ValueError("代码包含敏感信息，不应存储到向量记忆")

        # 生成唯一ID
        doc_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self._doc_counter}"
        self._doc_counter += 1

        # 构建文档内容
        document = f"需求: {requirement}\n\n代码:\n{code}"

        # 构建元数据
        doc_metadata = {
            "requirement": requirement,
            "code_length": len(code),
            "timestamp": datetime.now().isoformat(),
            **(metadata or {}),
        }

        # 添加到集合
        self.collection.add(
            documents=[document],
            metadatas=[doc_metadata],
            ids=[doc_id],
        )

        return doc_id

    def search(
        self,
        query: str,
        n_results: int = 5,
        where: Optional[dict] = None,
    ) -> list[dict[str, Any]]:
        """相似代码检索

        Args:
            query: 查询字符串
            n_results: 返回数量
            where: 元数据过滤条件

        Returns:
            检索结果列表
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where,
        )

        # 格式化结果
        formatted_results = []
        for i in range(len(results["ids"][0])):
            formatted_results.append({
                "id": results["ids"][0][i],
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "distance": results["distances"][0][i] if results.get("distances") else None,
            })

        return formatted_results

    def get_by_id(self, doc_id: str) -> Optional[dict[str, Any]]:
        """根据ID获取文档

        Args:
            doc_id: 文档ID

        Returns:
            文档内容
        """
        results = self.collection.get(ids=[doc_id])

        if not results["ids"]:
            return None

        return {
            "id": results["ids"][0],
            "document": results["documents"][0] if results["documents"] else "",
            "metadata": results["metadatas"][0] if results["metadatas"] else {},
        }

    def delete(self, doc_id: str) -> None:
        """删除文档

        Args:
            doc_id: 文档ID
        """
        self.collection.delete(ids=[doc_id])

    def clear(self) -> None:
        """清空所有记忆"""
        # 获取所有ID
        all_ids = self.collection.get()["ids"]
        if all_ids:
            self.collection.delete(ids=all_ids)
        self._doc_counter = 0

    def count(self) -> int:
        """获取记忆数量

        Returns:
            记忆条目数
        """
        return self.collection.count()

    def get_recent(self, n: int = 5) -> list[dict[str, Any]]:
        """获取最近的记忆

        Args:
            n: 返回数量

        Returns:
            最近的记忆列表
        """
        # 获取所有文档
        all_docs = self.collection.get()

        if not all_docs["ids"]:
            return []

        # 按时间戳排序
        docs_with_metadata = []
        for i in range(len(all_docs["ids"])):
            docs_with_metadata.append({
                "id": all_docs["ids"][i],
                "document": all_docs["documents"][i] if all_docs["documents"] else "",
                "metadata": all_docs["metadatas"][i] if all_docs["metadatas"] else {},
            })

        # 按时间戳降序排序
        docs_with_metadata.sort(
            key=lambda x: x["metadata"].get("timestamp", ""),
            reverse=True,
        )

        return docs_with_metadata[:n]


class HybridMemory:
    """混合记忆系统

    整合短期记忆和向量记忆。
    """

    def __init__(
        self,
        max_short_term: int = 100,
        persist_dir: str = "./memory/chroma",
        enable_vector: bool = True,
    ) -> None:
        """初始化混合记忆系统

        Args:
            max_short_term: 短期记忆最大条目数
            persist_dir: 向量记忆持久化目录
            enable_vector: 是否启用向量记忆
        """
        from .memory import ShortTermMemory

        self.short_term = ShortTermMemory(max_items=max_short_term)
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
        requirement: Optional[str] = None,
        code: Optional[str] = None,
    ) -> None:
        """添加记忆

        Args:
            key: 键名
            value: 值
            requirement: 需求描述（用于向量记忆）
            code: 代码内容（用于向量记忆）
        """
        # 添加到短期记忆
        self.short_term.add(key, value)

        # 添加到向量记忆
        if self.vector_memory and requirement and code:
            self.vector_memory.add(requirement, code)

    def search(self, query: str, k: int = 5) -> list[dict[str, Any]]:
        """搜索记忆

        Args:
            query: 查询字符串
            k: 返回数量

        Returns:
            匹配的记忆列表
        """
        results = []

        # 从短期记忆搜索
        short_term_results = self.short_term.search(query, k)
        results.extend(short_term_results)

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

    def clear(self) -> None:
        """清空所有记忆"""
        self.short_term.clear()
        if self.vector_memory:
            self.vector_memory.clear()

    @property
    def is_vector_enabled(self) -> bool:
        """向量记忆是否启用"""
        return self.vector_memory is not None
