# tests/test_code_generator.py
"""代码生成Agent单元测试"""

import pytest
from unittest.mock import Mock, MagicMock
from backend.agents.code_generator import CodeGeneratorAgent


class TestCodeGeneratorAgent:
    """CodeGeneratorAgent测试"""

    def test_create_generator(self):
        """测试创建生成器Agent"""
        llm = Mock()
        agent = CodeGeneratorAgent(llm=llm, tools=[])
        assert agent.name == "generator"

    def test_process_generate_request(self):
        """测试处理生成请求"""
        llm = Mock()
        llm.invoke.return_value = '''```python
def quick_sort(arr: list[int]) -> list[int]:
    """快速排序算法"""
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)
```'''

        agent = CodeGeneratorAgent(llm=llm, tools=[])
        result = agent.process(
            {"requirement": "实现快速排序算法"},
            {},
        )

        assert "code" in result
        assert "quick_sort" in result["code"]

    def test_extract_code_from_response(self):
        """测试从响应中提取代码"""
        llm = Mock()
        agent = CodeGeneratorAgent(llm=llm, tools=[])

        response = '''这是一个快速排序实现：
```python
def quick_sort(arr):
    pass
```
希望对你有帮助！'''

        code = agent._extract_code(response)
        assert "def quick_sort" in code
