# tests/test_integration.py
"""集成测试"""

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


class TestFullMultiAgentIntegration:
    """完整多Agent集成测试"""

    @patch("backend.llm.openai_llm.OpenAI")
    def test_full_multi_agent_workflow(self, mock_openai_class):
        """测试完整多Agent工作流"""
        from backend.core import Memory
        from backend.agents import (
            CodeGeneratorAgent,
            CodeReviewerAgent,
            DebuggerAgent,
        )

        # Mock OpenAI响应
        mock_client = Mock()

        # 生成代码的响应
        generate_response = Mock()
        generate_response.choices = [
            Mock(
                message=Mock(
                    content="```python\ndef divide(a, b):\n    return a / b\n```"
                )
            )
        ]

        # 第一次审查响应（不通过）
        review_response_1 = Mock()
        review_response_1.choices = [
            Mock(
                message=Mock(
                    content='{"passed": false, "issues": [{"severity": "high", "type": "bug", "line": 2, "message": "未处理除数为0"}], "score": 60}'
                )
            )
        ]

        # 修复代码的响应
        fix_response = Mock()
        fix_response.choices = [
            Mock(
                message=Mock(
                    content="```python\ndef divide(a, b):\n    if b == 0:\n        raise ValueError('除数不能为0')\n    return a / b\n```"
                )
            )
        ]

        # 第二次审查响应（通过）
        review_response_2 = Mock()
        review_response_2.choices = [
            Mock(
                message=Mock(
                    content='{"passed": true, "issues": [], "score": 95}'
                )
            )
        ]

        mock_client.chat.completions.create.side_effect = [
            generate_response,
            review_response_1,
            fix_response,
            review_response_2,
        ]
        mock_openai_class.return_value = mock_client

        # 创建完整的Agent系统
        llm = LLMFactory.create("openai", "gpt-4o-mini", api_key="test-key")

        generator = CodeGeneratorAgent(llm=llm, tools=[])
        reviewer = CodeReviewerAgent(llm=llm, tools=[])
        debugger = DebuggerAgent(llm=llm, tools=[])

        agents = {
            "generator": generator,
            "reviewer": reviewer,
            "debugger": debugger,
        }

        context = SharedContext()
        orchestrator = Orchestrator(agents=agents, context=context)

        # 执行请求
        result = orchestrator.process_request("实现一个除法函数")

        # 验证结果
        assert "code" in result
        assert "divide" in result["code"]
        assert orchestrator.state_machine.current_state == TaskState.DONE

    @patch("backend.llm.openai_llm.OpenAI")
    def test_tools_integration(self, mock_openai_class):
        """测试工具集成"""
        from backend.tools import ASTParser, CodeExecutor

        # 测试AST解析器
        parser = ASTParser()
        code = """
def add(a: int, b: int) -> int:
    return a + b
"""
        tree = parser.parse(code)
        functions = parser.extract_functions(tree)
        assert len(functions) == 1
        assert functions[0].name == "add"

        # 测试代码执行器
        executor = CodeExecutor(timeout=5)
        result = executor.execute("print(1 + 1)")
        assert result["success"] is True
        assert "2" in result["stdout"]

    def test_token_manager_integration(self):
        """测试Token管理器集成"""
        from backend.llm import TokenManager

        tm = TokenManager(max_tokens=1000)
        tm.track_usage(100)
        assert tm.current_usage == 100
        assert tm.get_remaining() == 900

        # 测试压缩判断
        short_text = "Hello"
        assert tm.should_compress(short_text) is False

        long_text = "x" * 5000
        assert tm.should_compress(long_text) is True
