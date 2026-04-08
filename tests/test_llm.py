# tests/test_llm.py
"""LLM抽象层单元测试"""

import pytest
from unittest.mock import Mock, patch
from backend.llm.base import BaseLLM, LLMFactory
from backend.llm.openai_llm import OpenAILLM


class TestBaseLLM:
    """BaseLLM抽象类测试"""

    def test_cannot_instantiate_base_class(self):
        """测试不能直接实例化抽象类"""
        with pytest.raises(TypeError):
            BaseLLM()


class TestOpenAILLM:
    """OpenAILLM测试"""

    def test_create_openai_llm(self):
        """测试创建OpenAI LLM实例"""
        llm = OpenAILLM(model="gpt-4", api_key="test-key")
        assert llm.model == "gpt-4"
        assert llm.api_key == "test-key"

    @patch("backend.llm.openai_llm.OpenAI")
    def test_invoke(self, mock_openai):
        """测试调用模型"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Hello, world!"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        llm = OpenAILLM(model="gpt-4", api_key="test-key")
        result = llm.invoke([{"role": "user", "content": "Hi"}])

        assert result == "Hello, world!"


class TestLLMFactory:
    """LLM工厂测试"""

    def test_create_openai_provider(self):
        """测试创建OpenAI provider"""
        llm = LLMFactory.create("openai", "gpt-4", api_key="test-key")
        assert isinstance(llm, OpenAILLM)

    def test_create_unknown_provider(self):
        """测试创建未知provider抛出异常"""
        with pytest.raises(ValueError, match="Unknown provider"):
            LLMFactory.create("unknown", "model")
