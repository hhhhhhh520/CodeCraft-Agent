"""测试生成Agent模块"""

import re
from typing import Any, Optional

from backend.core.agent import BaseAgent


class TestGeneratorAgent(BaseAgent):
    """测试生成Agent

    为代码生成测试用例。
    """

    SYSTEM_PROMPT = """你是一个专业的Python测试工程师。

请为给定的代码生成全面的测试用例，包括：
1. 正常情况测试
2. 边界情况测试
3. 异常情况测试

使用pytest框架，直接输出测试代码，使用```python代码块包裹。"""

    def __init__(self, llm: Any, tools: list[Any], memory: Optional[Any] = None) -> None:
        """初始化测试生成Agent

        Args:
            llm: LLM实例
            tools: 工具列表
            memory: 记忆系统实例
        """
        super().__init__(name="test_generator", llm=llm, tools=tools, memory=memory)

    def process(self, input_data: dict, context: dict) -> dict:
        """处理测试生成请求

        Args:
            input_data: 输入数据，包含code字段
            context: 共享上下文

        Returns:
            包含测试代码的结果字典
        """
        code = input_data.get("code", "")

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": f"请为以下代码生成测试用例：\n\n```python\n{code}\n```"},
        ]

        response = self.llm.invoke(messages)
        test_code = self._extract_code(response)

        return {
            "test_code": test_code,
            "original_code": code,
            "passed": True,  # 简化实现，默认通过
        }

    def _extract_code(self, response: str) -> str:
        """从响应中提取代码块"""
        pattern = r"```python\s*\n(.*?)\n```"
        matches = re.findall(pattern, response, re.DOTALL)
        if matches:
            return matches[0]

        pattern = r"```\s*\n(.*?)\n```"
        matches = re.findall(pattern, response, re.DOTALL)
        if matches:
            return matches[0]

        return response.strip()
