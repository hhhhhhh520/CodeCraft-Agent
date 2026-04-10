"""代码执行器单元测试"""

import pytest
from backend.tools.executor import CodeExecutor


class TestCodeExecutor:
    """CodeExecutor测试"""

    def test_execute_simple_code(self):
        """测试执行简单代码"""
        executor = CodeExecutor(timeout=5)
        code = "print('Hello')"
        result = executor.execute(code)

        assert result["success"] is True
        assert "Hello" in result["stdout"]

    def test_execute_with_return(self):
        """测试执行有返回值的代码"""
        executor = CodeExecutor(timeout=5)
        code = """
result = 1 + 1
print(result)
"""
        result = executor.execute(code)

        assert result["success"] is True
        assert "2" in result["stdout"]

    def test_execute_with_error(self):
        """测试执行有错误的代码"""
        executor = CodeExecutor(timeout=5)
        code = "1 / 0"
        result = executor.execute(code)

        assert result["success"] is False
        assert "ZeroDivisionError" in result["stderr"]

    def test_execute_timeout(self):
        """测试执行超时"""
        executor = CodeExecutor(timeout=1)
        code = """
import time
time.sleep(10)
"""
        result = executor.execute(code)

        assert result["success"] is False
        assert "timeout" in result.get("error", "").lower() or result.get("stderr", "")