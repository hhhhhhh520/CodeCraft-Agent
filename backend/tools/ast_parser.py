"""AST解析器模块"""

import ast
from typing import Any, Optional


class ASTParser:
    """Python AST解析器

    解析Python代码并提取结构信息。
    """

    def parse(self, code: str) -> ast.Module:
        """解析代码为AST

        Args:
            code: Python代码字符串

        Returns:
            AST模块节点

        Raises:
            SyntaxError: 代码语法错误
        """
        return ast.parse(code)

    def extract_functions(self, tree: ast.Module) -> list[ast.FunctionDef]:
        """提取所有函数定义

        Args:
            tree: AST模块节点

        Returns:
            函数定义节点列表
        """
        return [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]

    def extract_classes(self, tree: ast.Module) -> list[ast.ClassDef]:
        """提取所有类定义

        Args:
            tree: AST模块节点

        Returns:
            类定义节点列表
        """
        return [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]

    def extract_imports(self, tree: ast.Module) -> list[ast.stmt]:
        """提取所有导入

        Args:
            tree: AST模块节点

        Returns:
            导入节点列表
        """
        return [
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
        ]

    def get_function_signature(self, func: ast.FunctionDef) -> dict[str, Any]:
        """获取函数签名

        Args:
            func: 函数定义节点

        Returns:
            包含函数签名信息的字典
        """
        return {
            "name": func.name,
            "args": [arg.arg for arg in func.args.args],
            "defaults": [ast.unparse(d) if d else None for d in func.args.defaults],
            "returns": ast.unparse(func.returns) if func.returns else None,
            "docstring": ast.get_docstring(func),
        }

    def get_class_info(self, cls: ast.ClassDef) -> dict[str, Any]:
        """获取类信息

        Args:
            cls: 类定义节点

        Returns:
            包含类信息的字典
        """
        methods = [node.name for node in cls.body if isinstance(node, ast.FunctionDef)]
        return {
            "name": cls.name,
            "bases": [ast.unparse(base) for base in cls.bases],
            "methods": methods,
            "docstring": ast.get_docstring(cls),
        }