# tests/test_context.py
"""共享上下文单元测试"""

import pytest
from backend.core.context import SharedContext


class TestSharedContext:
    """SharedContext测试"""

    def test_create_context(self):
        """测试创建上下文"""
        ctx = SharedContext()
        assert ctx.data == {}

    def test_set_and_get(self):
        """测试设置和获取数据"""
        ctx = SharedContext()
        ctx.set("user_request", "generate a function")
        assert ctx.get("user_request") == "generate a function"

    def test_get_nonexistent_key(self):
        """测试获取不存在的键"""
        ctx = SharedContext()
        assert ctx.get("nonexistent") is None
        assert ctx.get("nonexistent", default="default") == "default"

    def test_update(self):
        """测试批量更新"""
        ctx = SharedContext()
        ctx.update({"key1": "value1", "key2": "value2"})
        assert ctx.get("key1") == "value1"
        assert ctx.get("key2") == "value2"

    def test_clear(self):
        """测试清空上下文"""
        ctx = SharedContext()
        ctx.set("key", "value")
        ctx.clear()
        assert ctx.data == {}

    def test_task_id(self):
        """测试任务ID"""
        ctx = SharedContext()
        assert ctx.task_id is not None
        ctx2 = SharedContext()
        assert ctx.task_id != ctx2.task_id
