"""代码处理工具模块"""

import re
from typing import Optional


def extract_code_from_response(response: str) -> str:
    """从LLM响应中提取代码块

    支持多种格式的代码块提取：
    1. ```python ... ```
    2. ``` ... ```
    3. 无代码块时返回原始响应

    Args:
        response: LLM响应文本

    Returns:
        提取的代码文本，如无代码块则返回原始响应
    """
    if not response:
        return ""

    # 优先匹配 ```python ... ``` 代码块
    python_pattern = r"```python\s*\n(.*?)\n```"
    python_matches = re.findall(python_pattern, response, re.DOTALL)
    if python_matches:
        return python_matches[0].strip()

    # 匹配通用的 ``` ... ``` 代码块
    generic_pattern = r"```\s*\n(.*?)\n```"
    generic_matches = re.findall(generic_pattern, response, re.DOTALL)
    if generic_matches:
        return generic_matches[0].strip()

    # 如果没有代码块，返回原始响应（去除首尾空白）
    return response.strip()


def validate_python_code(code: str) -> tuple[bool, Optional[str]]:
    """验证Python代码语法

    Args:
        code: Python代码字符串

    Returns:
        (是否有效, 错误消息) 元组
    """
    if not code:
        return False, "代码为空"

    try:
        compile(code, "<string>", "exec")
        return True, None
    except SyntaxError as e:
        return False, f"语法错误: 第{e.lineno}行 - {e.msg}"


def count_code_lines(code: str) -> dict[str, int]:
    """统计代码行数信息

    Args:
        code: Python代码字符串

    Returns:
        包含总行数、代码行数、注释行数、空行数的字典
    """
    if not code:
        return {"total": 0, "code": 0, "comments": 0, "blank": 0}

    lines = code.split("\n")
    total = len(lines)
    code_lines = 0
    comment_lines = 0
    blank_lines = 0

    for line in lines:
        stripped = line.strip()
        if not stripped:
            blank_lines += 1
        elif stripped.startswith("#"):
            comment_lines += 1
        else:
            code_lines += 1

    return {
        "total": total,
        "code": code_lines,
        "comments": comment_lines,
        "blank": blank_lines,
    }
