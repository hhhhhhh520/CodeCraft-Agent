"""Token管理器单元测试"""

import pytest
from backend.llm.token_manager import TokenManager


class TestTokenManager:
    """TokenManager测试"""

    def test_create_token_manager(self):
        """测试创建Token管理器"""
        tm = TokenManager(max_tokens=1000)
        assert tm.max_tokens == 1000
        assert tm.current_usage == 0

    def test_estimate_tokens(self):
        """测试估算Token数"""
        tm = TokenManager()
        text = "Hello, world!"
        tokens = tm.estimate_tokens(text)
        assert tokens > 0

    def test_should_compress(self):
        """测试判断是否需要压缩"""
        tm = TokenManager(max_tokens=100)
        # 短文本不需要压缩
        assert tm.should_compress("short text") is False
        # 长文本需要压缩
        long_text = "x" * 400
        assert tm.should_compress(long_text) is True

    def test_track_usage(self):
        """测试追踪Token使用量"""
        tm = TokenManager()
        tm.track_usage(100)
        assert tm.current_usage == 100
        tm.track_usage(50)
        assert tm.current_usage == 150

    def test_get_remaining(self):
        """测试获取剩余Token数"""
        tm = TokenManager(max_tokens=1000)
        tm.track_usage(300)
        assert tm.get_remaining() == 700

    def test_reset(self):
        """测试重置使用量"""
        tm = TokenManager()
        tm.track_usage(100)
        tm.reset()
        assert tm.current_usage == 0
