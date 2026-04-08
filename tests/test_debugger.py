"""调试Agent单元测试"""

import pytest
from unittest.mock import Mock
from backend.agents.debugger import DebuggerAgent


class TestDebuggerAgent:
    """DebuggerAgent测试"""

    def test_create_debugger(self):
        """测试创建调试Agent"""
        llm = Mock()
        agent = DebuggerAgent(llm=llm, tools=[])
        assert agent.name == "debugger"

    def test_fix_code(self):
        """测试修复代码"""
        llm = Mock()
        llm.invoke.return_value = '''```python
def divide(a: int, b: int) -> float:
    """除法运算"""
    if b == 0:
        raise ValueError("除数不能为0")
    return a / b
```'''

        agent = DebuggerAgent(llm=llm, tools=[])
        result = agent.process(
            {
                "code": "def divide(a, b):\n    return a / b",
                "issues": [
                    {
                        "severity": "high",
                        "type": "bug",
                        "line": 2,
                        "message": "未处理除数为0的情况",
                        "suggestion": "添加除数检查",
                    }
                ],
            },
            {},
        )

        assert "fixed_code" in result
        assert "divide" in result["fixed_code"]
