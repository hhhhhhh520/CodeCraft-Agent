# tests/test_code_reviewer.py
"""代码审查Agent单元测试"""

import pytest
from unittest.mock import Mock
from backend.agents.code_reviewer import CodeReviewerAgent


class TestCodeReviewerAgent:
    """CodeReviewerAgent测试"""

    def test_create_reviewer(self):
        """测试创建审查Agent"""
        llm = Mock()
        agent = CodeReviewerAgent(llm=llm, tools=[])
        assert agent.name == "reviewer"

    def test_review_good_code(self):
        """测试审查良好代码"""
        llm = Mock()
        llm.invoke.return_value = '''{
            "passed": true,
            "issues": [],
            "score": 95,
            "summary": "代码质量良好"
        }'''

        agent = CodeReviewerAgent(llm=llm, tools=[])
        result = agent.process(
            {"code": "def add(a: int, b: int) -> int:\n    return a + b"},
            {},
        )

        assert result["passed"] is True
        assert result["score"] == 95

    def test_review_bad_code(self):
        """测试审查问题代码"""
        llm = Mock()
        llm.invoke.return_value = '''{
            "passed": false,
            "issues": [
                {
                    "severity": "high",
                    "type": "security",
                    "line": 1,
                    "message": "SQL注入风险",
                    "suggestion": "使用参数化查询"
                }
            ],
            "score": 60,
            "summary": "存在安全隐患"
        }'''

        agent = CodeReviewerAgent(llm=llm, tools=[])
        result = agent.process(
            {"code": "query = f'SELECT * FROM users WHERE id = {user_id}'"},
            {},
        )

        assert result["passed"] is False
        assert len(result["issues"]) == 1
        assert result["issues"][0]["severity"] == "high"
