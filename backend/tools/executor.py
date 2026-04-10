"""代码执行器模块"""

import os
import subprocess
import sys
import tempfile
from typing import Any, Optional


class CodeExecutor:
    """代码执行器

    在沙箱环境中安全执行Python代码。
    """

    def __init__(self, timeout: int = 30) -> None:
        """初始化执行器

        Args:
            timeout: 执行超时时间（秒）
        """
        self.timeout = timeout

    def execute(self, code: str) -> dict[str, Any]:
        """执行代码

        Args:
            code: Python代码字符串

        Returns:
            执行结果字典，包含success、stdout、stderr等字段
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            result = subprocess.run(
                [sys.executable, temp_path],  # 使用sys.executable确保跨环境兼容
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=self._get_safe_env(),
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
                "error": f"Execution timeout after {self.timeout} seconds",
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

        finally:
            os.unlink(temp_path)

    def _get_safe_env(self) -> dict[str, str]:
        """获取安全的环境变量

        使用最小权限原则，仅提供必要的系统路径。

        Returns:
            安全的环境变量字典
        """
        # 安全的PATH配置：仅包含必要的系统目录
        # 注意：这里使用受限路径，避免暴露用户的完整PATH
        safe_path = "/usr/bin:/bin" if sys.platform != "win32" else os.path.dirname(sys.executable)

        return {
            "PATH": safe_path,
            "PYTHONPATH": "",  # 禁止导入用户自定义模块
            "PYTHONIOENCODING": "utf-8",
            "HOME": os.environ.get("HOME", ""),
            "TEMP": os.environ.get("TEMP", "/tmp"),
        }