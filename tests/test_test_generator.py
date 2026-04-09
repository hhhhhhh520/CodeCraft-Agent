"""测试生成Agent单元测试"""

import pytest
from unittest.mock import Mock
from backend.agents.test_generator import TestGeneratorAgent


class TestTestGeneratorAgent:
    """TestGeneratorAgent测试"""

    def test_create_test_generator(self):
        """测试创建测试生成Agent"""
        llm = Mock()
        agent = TestGeneratorAgent(llm=llm, tools=[])
        assert agent.name == "test_generator"

    def test_generate_tests(self):
        """测试生成测试用例"""
        llm = Mock()
        llm.invoke.return_value = '''```python
import pytest
from my_module import add

def test_add_positive():
    assert add(1, 2) == 3

def test_add_negative():
    assert add(-1, -1) == -2

def test_add_zero():
    assert add(0, 0) == 0
```'''

        agent = TestGeneratorAgent(llm=llm, tools=[])
        result = agent.process(
            {"code": "def add(a: int, b: int) -> int:\n    return a + b"},
            {},
        )

        assert "test_code" in result
        assert "test_add" in result["test_code"]

    def test_generate_tests_with_class(self):
        """测试为类生成测试用例"""
        llm = Mock()
        llm.invoke.return_value = '''```python
import pytest
from my_module import Calculator

class TestCalculator:
    def test_add(self):
        calc = Calculator()
        assert calc.add(1, 2) == 3
```'''

        agent = TestGeneratorAgent(llm=llm, tools=[])
        result = agent.process(
            {"code": "class Calculator:\n    def add(self, a, b):\n        return a + b"},
            {},
        )

        assert "test_code" in result
        assert "TestCalculator" in result["test_code"]
