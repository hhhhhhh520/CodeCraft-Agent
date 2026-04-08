# tests/test_agent.py
"""Agent基类单元测试"""

import pytest
from unittest.mock import Mock
from backend.core.agent import BaseAgent


class ConcreteAgent(BaseAgent):
    """测试用具体Agent实现"""

    def process(self, input_data: dict, context: dict) -> dict:
        return {"result": f"processed: {input_data.get('task', 'unknown')}"}


class TestBaseAgent:
    """BaseAgent测试"""

    def test_create_agent(self):
        """测试创建Agent实例"""
        llm = Mock()
        agent = ConcreteAgent(name="test_agent", llm=llm, tools=[])
        assert agent.name == "test_agent"
        assert agent.llm == llm
        assert agent.tools == []

    def test_agent_process(self):
        """测试Agent处理任务"""
        llm = Mock()
        agent = ConcreteAgent(name="test_agent", llm=llm, tools=[])
        result = agent.process({"task": "generate"}, {})
        assert result == {"result": "processed: generate"}

    def test_agent_observe(self):
        """测试Agent观察方法"""
        llm = Mock()
        agent = ConcreteAgent(name="test_agent", llm=llm, tools=[])
        observation = agent.observe({"state": "running"})
        assert observation == {"observation": {"state": "running"}}

    def test_agent_with_tools(self):
        """测试Agent携带工具"""
        llm = Mock()
        tool1 = Mock()
        tool2 = Mock()
        agent = ConcreteAgent(name="test_agent", llm=llm, tools=[tool1, tool2])
        assert len(agent.tools) == 2
