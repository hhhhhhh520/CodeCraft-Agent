# tests/test_integration.py
"""Phase 1 集成测试"""

import pytest
from unittest.mock import Mock, patch
from backend.core import Orchestrator, SharedContext, TaskState
from backend.agents import CodeGeneratorAgent
from backend.llm.base import LLMFactory


class TestPhase1Integration:
    """Phase 1 集成测试"""

    @patch("backend.llm.openai_llm.OpenAI")
    def test_full_workflow(self, mock_openai_class):
        """测试完整工作流"""
        # Mock OpenAI响应
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content="```python\ndef hello():\n    print('Hello')\n```"))
        ]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        # 创建LLM
        llm = LLMFactory.create("openai", "gpt-4o-mini", api_key="test-key")

        # 创建Agent
        generator = CodeGeneratorAgent(llm=llm, tools=[])

        # 创建Orchestrator
        agents = {"generator": generator}
        context = SharedContext()
        orchestrator = Orchestrator(agents=agents, context=context)

        # 处理请求
        result = orchestrator.process_request("实现一个hello函数")

        # 验证结果
        assert "code" in result
        assert "hello" in result["code"].lower()
        assert orchestrator.state_machine.current_state == TaskState.DONE

    def test_state_machine_full_cycle(self):
        """测试状态机完整周期"""
        from backend.core import StateMachine

        sm = StateMachine()

        # PENDING -> ANALYZING
        assert sm.transition(TaskState.ANALYZING) is True
        # ANALYZING -> GENERATING
        assert sm.transition(TaskState.GENERATING) is True
        # GENERATING -> REVIEWING
        assert sm.transition(TaskState.REVIEWING) is True
        # REVIEWING -> DONE (跳过测试)
        assert sm.transition(TaskState.DONE) is True

        assert sm.current_state == TaskState.DONE
