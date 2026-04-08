"""记忆系统单元测试"""

import pytest
from backend.core.memory import Memory, ShortTermMemory


class TestShortTermMemory:
    """ShortTermMemory测试"""

    def test_add_and_search(self):
        """测试添加和搜索"""
        memory = ShortTermMemory(max_items=10)
        memory.add("key1", "value1")
        memory.add("key2", "value2")

        result = memory.search("key", k=5)
        assert len(result) == 2

    def test_max_items_limit(self):
        """测试最大条目限制"""
        memory = ShortTermMemory(max_items=3)
        memory.add("key1", "value1")
        memory.add("key2", "value2")
        memory.add("key3", "value3")
        memory.add("key4", "value4")

        assert len(memory.items) == 3
        assert memory.items[0]["key"] == "key2"


class TestMemory:
    """Memory测试"""

    def test_short_term_memory(self):
        """测试短期记忆"""
        memory = Memory()
        memory.add("session_key", "session_value", memory_type="short")

        result = memory.recall("session", k=5)
        assert len(result) > 0

    def test_get_recent(self):
        """测试获取最近记忆"""
        memory = Memory()
        memory.add("key1", "value1")
        memory.add("key2", "value2")

        recent = memory.get_recent(n=2)
        assert len(recent) == 2
