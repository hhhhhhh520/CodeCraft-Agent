"""向量记忆系统测试"""

import os
import tempfile
import pytest
import shutil

# 跳过测试如果ChromaDB未安装
pytest.importorskip("chromadb")

from backend.core.vector_memory import VectorMemory, HybridMemory, CHROMADB_AVAILABLE


class TestVectorMemory:
    """VectorMemory测试类"""

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        tmpdir = tempfile.mkdtemp()
        yield tmpdir
        # Windows上ChromaDB可能仍持有文件句柄，忽略清理错误
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass

    @pytest.fixture
    def vector_memory(self, temp_dir):
        """创建VectorMemory实例"""
        return VectorMemory(persist_dir=temp_dir)

    def test_chromadb_available(self):
        """测试ChromaDB是否可用"""
        assert CHROMADB_AVAILABLE, "ChromaDB应该可用"

    def test_init(self, vector_memory):
        """测试初始化"""
        assert vector_memory is not None
        assert vector_memory.count() == 0

    def test_add(self, vector_memory):
        """测试添加记忆"""
        doc_id = vector_memory.add(
            requirement="实现快速排序",
            code="def quick_sort(arr): ...",
        )

        assert doc_id is not None
        assert vector_memory.count() == 1

    def test_search(self, vector_memory):
        """测试搜索"""
        # 添加多个记忆
        vector_memory.add("实现快速排序", "def quick_sort(arr): ...")
        vector_memory.add("实现二分查找", "def binary_search(arr, target): ...")
        vector_memory.add("实现冒泡排序", "def bubble_sort(arr): ...")

        # 搜索排序相关
        results = vector_memory.search("排序算法", n_results=2)

        assert len(results) == 2
        assert "排序" in results[0]["document"] or "排序" in results[1]["document"]

    def test_get_by_id(self, vector_memory):
        """测试根据ID获取"""
        doc_id = vector_memory.add("测试需求", "print('hello')")

        result = vector_memory.get_by_id(doc_id)

        assert result is not None
        assert "测试需求" in result["document"]

    def test_delete(self, vector_memory):
        """测试删除"""
        doc_id = vector_memory.add("测试需求", "print('hello')")
        assert vector_memory.count() == 1

        vector_memory.delete(doc_id)
        assert vector_memory.count() == 0

    def test_clear(self, vector_memory):
        """测试清空"""
        vector_memory.add("需求1", "code1")
        vector_memory.add("需求2", "code2")
        assert vector_memory.count() == 2

        vector_memory.clear()
        assert vector_memory.count() == 0

    def test_get_recent(self, vector_memory):
        """测试获取最近记忆"""
        vector_memory.add("需求1", "code1")
        vector_memory.add("需求2", "code2")
        vector_memory.add("需求3", "code3")

        recent = vector_memory.get_recent(2)

        assert len(recent) == 2


class TestHybridMemory:
    """HybridMemory测试类"""

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        tmpdir = tempfile.mkdtemp()
        yield tmpdir
        # Windows上ChromaDB可能仍持有文件句柄，忽略清理错误
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass

    @pytest.fixture
    def hybrid_memory(self, temp_dir):
        """创建HybridMemory实例"""
        return HybridMemory(persist_dir=temp_dir, enable_vector=True)

    def test_init(self, hybrid_memory):
        """测试初始化"""
        assert hybrid_memory is not None
        assert hybrid_memory.short_term is not None
        assert hybrid_memory.is_vector_enabled

    def test_add(self, hybrid_memory):
        """测试添加记忆"""
        hybrid_memory.add(
            key="test",
            value={"code": "print('hello')"},
            requirement="测试需求",
            code="print('hello')",
        )

        # 检查短期记忆
        assert len(hybrid_memory.short_term.items) == 1

    def test_search(self, hybrid_memory):
        """测试搜索"""
        hybrid_memory.add(
            key="sort",
            value={},
            requirement="实现快速排序",
            code="def quick_sort(arr): ...",
        )

        results = hybrid_memory.search("排序", k=5)

        assert len(results) >= 1

    def test_get_recent(self, hybrid_memory):
        """测试获取最近记忆"""
        hybrid_memory.add("key1", "value1")
        hybrid_memory.add("key2", "value2")

        recent = hybrid_memory.get_recent(2)

        assert len(recent) == 2

    def test_clear(self, hybrid_memory):
        """测试清空"""
        hybrid_memory.add("key1", "value1")
        hybrid_memory.clear()

        assert len(hybrid_memory.short_term.items) == 0
