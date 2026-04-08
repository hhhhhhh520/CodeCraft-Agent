# tests/test_orchestrator.py
"""Orchestrator单元测试"""

import pytest
from unittest.mock import Mock, MagicMock
from backend.core.orchestrator import Orchestrator
from backend.core.state import TaskState
from backend.core.context import SharedContext


class TestOrchestrator:
    """Orchestrator测试"""

    def test_create_orchestrator(self):
        """测试创建Orchestrator"""
        generator = Mock()
        generator.name = "generator"

        agents = {"generator": generator}
        ctx = SharedContext()
        orch = Orchestrator(agents=agents, context=ctx)

        assert orch.agents == agents
        assert orch.context == ctx
        assert orch.state_machine.current_state == TaskState.PENDING

    def test_process_request_generating(self):
        """测试处理生成请求"""
        generator = Mock()
        generator.name = "generator"
        generator.process.return_value = {
            "code": "def hello(): pass",
            "raw_response": "code",
        }

        agents = {"generator": generator}
        ctx = SharedContext()
        orch = Orchestrator(agents=agents, context=ctx)

        result = orch.process_request("实现一个hello函数")

        assert "code" in result
        generator.process.assert_called_once()

    def test_state_transitions(self):
        """测试状态转换"""
        generator = Mock()
        generator.name = "generator"
        generator.process.return_value = {"code": "pass"}

        agents = {"generator": generator}
        ctx = SharedContext()
        orch = Orchestrator(agents=agents, context=ctx)

        # 初始状态
        assert orch.state_machine.current_state == TaskState.PENDING

        # 处理请求后状态变化
        orch.process_request("test")
        assert orch.state_machine.current_state == TaskState.DONE
