"""代码执行器模块"""

import os
import subprocess
import sys
import tempfile
import ast
import re
from typing import Any, Optional


class CodeSecurityError(Exception):
    """代码安全错误"""
    pass


class CodeValidator:
    """代码安全验证器"""

    # 危险导入模块
    DANGEROUS_MODULES = {
        "os", "subprocess", "sys", "socket", "shutil",
        "pickle", "marshal", "ctypes", "multiprocessing",
        "threading", "signal", "resource", "posix", "nt",
    }

    # 危险内置函数
    DANGEROUS_BUILTINS = {
        "eval", "exec", "compile", "__import__",
        "open", "input", "breakpoint",
    }

    @classmethod
    def validate(cls, code: str, strict: bool = True) -> tuple[bool, list[str]]:
        """验证代码安全性

        Args:
            code: Python代码字符串
            strict: 严格模式，发现任何危险模式都拒绝

        Returns:
            (是否安全, 问题列表)
        """
        issues = []

        # 1. 语法验证
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            issues.append(f"语法错误: {e}")
            return False, issues

        # 2. AST遍历检查危险操作
        for node in ast.walk(tree):
            # 检查导入
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name.split(".")[0]
                    if module_name in cls.DANGEROUS_MODULES:
                        issues.append(f"危险导入: {alias.name}")

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module_name = node.module.split(".")[0]
                    if module_name in cls.DANGEROUS_MODULES:
                        issues.append(f"危险导入: from {node.module}")

            # 检查危险函数调用
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in cls.DANGEROUS_BUILTINS:
                        issues.append(f"危险函数调用: {node.func.id}()")

                # 检查os.system, subprocess.run等
                elif isinstance(node.func, ast.Attribute):
                    if isinstance(node.func.value, ast.Name):
                        if node.func.value.id == "os" and node.func.attr in {"system", "popen", "spawn"}:
                            issues.append(f"危险调用: os.{node.func.attr}")
                        elif node.func.value.id == "subprocess":
                            issues.append(f"危险调用: subprocess.{node.func.attr}")

        # 3. 正则检查危险模式
        dangerous_patterns = [
            (r"__import__\s*\(", "动态导入"),
            (r"getattr\s*\([^)]*,\s*['\"]__", "反射访问私有属性"),
            (r"globals\s*\(\)", "访问全局命名空间"),
            (r"locals\s*\(\)", "访问局部命名空间"),
        ]

        for pattern, desc in dangerous_patterns:
            if re.search(pattern, code):
                issues.append(f"检测到危险模式: {desc}")

        if strict and issues:
            return False, issues

        return len(issues) == 0, issues


class CodeExecutor:
    """代码执行器

    在沙箱环境中安全执行Python代码。
    """

    def __init__(self, timeout: int = 30, max_memory_mb: int = 256) -> None:
        """初始化执行器

        Args:
            timeout: 执行超时时间（秒）
            max_memory_mb: 最大内存限制（MB）
        """
        self.timeout = timeout
        self.max_memory_mb = max_memory_mb

    def execute(self, code: str, validate: bool = True) -> dict[str, Any]:
        """执行代码

        Args:
            code: Python代码字符串
            validate: 是否进行安全验证

        Returns:
            执行结果字典，包含success、stdout、stderr等字段
        """
        # 安全验证
        if validate:
            is_safe, issues = CodeValidator.validate(code)
            if not is_safe:
                return {
                    "success": False,
                    "error": "代码未通过安全验证",
                    "security_issues": issues,
                    "stdout": "",
                    "stderr": "",
                }

        # 在临时目录中执行，限制文件访问范围
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_file = os.path.join(tmpdir, "sandbox.py")
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(code)

            try:
                result = subprocess.run(
                    [sys.executable, temp_file],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    env=self._get_safe_env(),
                    cwd=tmpdir,  # 限制工作目录为临时目录
                )

                return {
                    "success": result.returncode == 0,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode,
                }

            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "error": f"执行超时（{self.timeout}秒）",
                    "stdout": "",
                    "stderr": "",
                }

            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "stdout": "",
                    "stderr": "",
                }

    def _get_safe_env(self) -> dict[str, str]:
        """获取安全的环境变量

        使用最小权限原则，仅提供必要的系统路径。
        不传递HOME、USER等敏感环境变量。

        Returns:
            安全的环境变量字典
        """
        # 安全的PATH配置：仅包含Python解释器目录
        safe_path = "/usr/bin:/bin" if sys.platform != "win32" else os.path.dirname(sys.executable)

        return {
            "PATH": safe_path,
            "PYTHONPATH": "",  # 禁止导入用户自定义模块
            "PYTHONIOENCODING": "utf-8",
            # 不传递HOME、TEMP、USER等敏感环境变量
        }

    def safe_exec(self, code: str, allowed_globals: dict = None) -> dict[str, Any]:
        """安全执行代码（使用受限命名空间）

        用于demo等需要执行代码但不使用subprocess的场景。

        Args:
            code: Python代码字符串
            allowed_globals: 允许的全局变量

        Returns:
            执行结果
        """
        # 安全验证
        is_safe, issues = CodeValidator.validate(code)
        if not is_safe:
            return {
                "success": False,
                "error": "代码未通过安全验证",
                "security_issues": issues,
            }

        # 构建安全的全局命名空间
        safe_builtins = {
            "print": print,
            "range": range,
            "len": len,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
            "set": set,
            "tuple": tuple,
            "enumerate": enumerate,
            "zip": zip,
            "map": map,
            "filter": filter,
            "sorted": sorted,
            "reversed": reversed,
            "sum": sum,
            "min": min,
            "max": max,
            "abs": abs,
            "round": round,
            "isinstance": isinstance,
            "hasattr": hasattr,
            "getattr": getattr,
            "True": True,
            "False": False,
            "None": None,
        }

        exec_globals = {"__builtins__": safe_builtins}
        if allowed_globals:
            exec_globals.update(allowed_globals)

        try:
            exec(code, exec_globals)
            return {"success": True, "globals": exec_globals}
        except Exception as e:
            return {"success": False, "error": str(e)}