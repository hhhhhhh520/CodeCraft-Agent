"""create_orchestrator 装配工厂测试"""

from unittest.mock import Mock, patch

from backend.core.factory import create_orchestrator


class TestCreateOrchestrator:
    """create_orchestrator 装配测试"""

    @patch("backend.core.factory.LLMFactory")
    def test_full_mode_registers_four_agents(self, mock_factory):
        """完整模式注册 generator/reviewer/debugger/test_generator 四个Agent"""
        mock_llm = Mock()
        mock_factory.create.return_value = mock_llm

        orch = create_orchestrator(api_key="test-key", model="test-model")

        assert set(orch.agents.keys()) == {
            "generator",
            "reviewer",
            "debugger",
            "test_generator",
        }
        # 所有Agent共享同一个LLM实例
        assert all(agent.llm is mock_llm for agent in orch.agents.values())

    @patch("backend.core.factory.LLMFactory")
    def test_fast_mode_registers_generator_only(self, mock_factory):
        """快速模式只注册 generator"""
        mock_factory.create.return_value = Mock()

        orch = create_orchestrator(api_key="test-key", model="test-model", fast=True)

        assert set(orch.agents.keys()) == {"generator"}

    @patch("backend.core.factory.LLMFactory")
    def test_llm_created_with_given_endpoint(self, mock_factory):
        """LLM 按调用方传入的 api_key/model/base_url 创建"""
        mock_factory.create.return_value = Mock()

        create_orchestrator(
            api_key="key-1", model="model-1", base_url="https://example.com/v1"
        )

        assert mock_factory.create.call_args.args == ("openai", "model-1")
        kwargs = mock_factory.create.call_args.kwargs
        assert kwargs["api_key"] == "key-1"
        assert kwargs["base_url"] == "https://example.com/v1"
