"""代码工具模块测试"""

import pytest
from backend.utils.code_utils import extract_code_from_response, validate_python_code, count_code_lines


class TestExtractCodeFromResponse:
    """extract_code_from_response测试"""

    def test_python_code_block(self):
        """测试提取python代码块"""
        response = "这是代码：\n```python\ndef hello():\n    print('hello')\n```\n结束"
        result = extract_code_from_response(response)
        assert "def hello():" in result
        assert "print('hello')" in result

    def test_generic_code_block(self):
        """测试提取通用代码块"""
        response = "```\ndef hello():\n    pass\n```"
        result = extract_code_from_response(response)
        assert "def hello():" in result

    def test_multiple_python_blocks(self):
        """测试多个代码块时提取第一个"""
        response = "```python\ndef a(): pass\n```\n```python\ndef b(): pass\n```"
        result = extract_code_from_response(response)
        assert "def a():" in result

    def test_no_code_block(self):
        """测试无代码块时返回空字符串"""
        response = "def hello(): pass"
        result = extract_code_from_response(response)
        assert result == ""

    def test_empty_response(self):
        """测试空响应"""
        assert extract_code_from_response("") == ""
        assert extract_code_from_response(None) == ""

    def test_whitespace_handling(self):
        """测试空白处理"""
        response = "```python\ndef hello():\n    pass\n```"
        result = extract_code_from_response(response)
        assert not result.startswith("\n")
        assert not result.endswith("\n")

    def test_nested_backticks(self):
        """测试嵌套反引号"""
        response = '```python\nprint("```")\n```'
        result = extract_code_from_response(response)
        assert 'print("```")' in result


class TestValidatePythonCode:
    """validate_python_code测试"""

    def test_valid_code(self):
        """测试有效代码"""
        is_valid, error = validate_python_code("def hello(): pass")
        assert is_valid is True
        assert error is None

    def test_syntax_error(self):
        """测试语法错误"""
        is_valid, error = validate_python_code("def hello(")
        assert is_valid is False
        assert "语法错误" in error

    def test_empty_code(self):
        """测试空代码"""
        is_valid, error = validate_python_code("")
        assert is_valid is False
        assert error == "代码为空"

    def test_none_code(self):
        """测试None输入"""
        is_valid, error = validate_python_code(None)
        assert is_valid is False

    def test_complex_valid_code(self):
        """测试复杂有效代码"""
        code = """
import os
from pathlib import Path

class MyClass:
    def __init__(self, name: str):
        self.name = name

    def greet(self) -> str:
        return f"Hello, {self.name}!"
"""
        is_valid, error = validate_python_code(code)
        assert is_valid is True


class TestCountCodeLines:
    """count_code_lines测试"""

    def test_basic_count(self):
        """测试基本行数统计"""
        code = "def hello():\n    pass"
        result = count_code_lines(code)
        assert result["total"] == 2
        assert result["code"] == 2
        assert result["comments"] == 0
        assert result["blank"] == 0

    def test_with_comments(self):
        """测试含注释的代码"""
        code = "# 注释\ndef hello():\n    pass"
        result = count_code_lines(code)
        assert result["comments"] == 1
        assert result["code"] == 2

    def test_with_blank_lines(self):
        """测试含空行的代码"""
        code = "def hello():\n\n    pass"
        result = count_code_lines(code)
        assert result["blank"] == 1

    def test_empty_code(self):
        """测试空代码"""
        result = count_code_lines("")
        assert result["total"] == 0
        assert result["code"] == 0

    def test_none_code(self):
        """测试None输入"""
        result = count_code_lines(None)
        assert result["total"] == 0
