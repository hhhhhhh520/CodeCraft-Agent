"""AST解析器单元测试"""

import pytest
from backend.tools.ast_parser import ASTParser


class TestASTParser:
    """ASTParser测试"""

    def test_parse_simple_code(self):
        """测试解析简单代码"""
        code = """
def hello():
    print("Hello, World!")
"""
        parser = ASTParser()
        tree = parser.parse(code)
        assert tree is not None

    def test_extract_functions(self):
        """测试提取函数"""
        code = """
def func1():
    pass

def func2(a: int) -> str:
    return str(a)
"""
        parser = ASTParser()
        tree = parser.parse(code)
        functions = parser.extract_functions(tree)

        assert len(functions) == 2
        assert functions[0].name == "func1"
        assert functions[1].name == "func2"

    def test_extract_classes(self):
        """测试提取类"""
        code = """
class MyClass:
    def method(self):
        pass
"""
        parser = ASTParser()
        tree = parser.parse(code)
        classes = parser.extract_classes(tree)

        assert len(classes) == 1
        assert classes[0].name == "MyClass"

    def test_get_function_signature(self):
        """测试获取函数签名"""
        code = """
def add(a: int, b: int) -> int:
    '''Add two numbers.'''
    return a + b
"""
        parser = ASTParser()
        tree = parser.parse(code)
        functions = parser.extract_functions(tree)
        sig = parser.get_function_signature(functions[0])

        assert sig["name"] == "add"
        assert sig["args"] == ["a", "b"]
        assert sig["returns"] == "int"
        assert sig["docstring"] == "Add two numbers."