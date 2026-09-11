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
        # 支持中英文错误消息
        error_msg = result.get("error", "").lower()
        assert "timeout" in error_msg or "超时" in error_msg or result.get("stderr", "")

    def test_execute_chinese_output_not_mojibake(self):
        """中文输出必须按 UTF-8 解码，不得出现 GBK 乱码

        回归背景：sandbox 子进程被 _get_safe_env() 的 PYTHONIOENCODING=utf-8
        强制为 UTF-8 输出，而父进程 subprocess.run(text=True) 在中文 Windows
        上默认按 GBK 解码 —— 轻则乱码（'鎺掑簭瀹屾垚'），重则 reader 线程抛
        UnicodeDecodeError 导致 stdout/stderr 全部丢失。
        """
        executor = CodeExecutor(timeout=10)
        code = "print('排序完成：[1, 2, 3]')"
        result = executor.execute(code, validate=False)

        assert result["success"] is True
        assert "排序完成：[1, 2, 3]" in result["stdout"]
        assert "鎺" not in result["stdout"]  # UTF-8 字节被误读成 GBK 的典型乱码

    def test_execute_chinese_error_message_readable(self):
        """中文报错的 traceback 必须可读（此前会触发 UnicodeDecodeError 丢 stderr）"""
        executor = CodeExecutor(timeout=10)
        code = 'raise TypeError("列表中的所有元素必须为整数。")'
        result = executor.execute(code, validate=False)

        assert result["success"] is False
        assert "列表中的所有元素必须为整数。" in result["stderr"]