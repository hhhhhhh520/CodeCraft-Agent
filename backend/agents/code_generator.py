"""代码生成Agent模块"""

import re
from typing import Any, Optional

from backend.core.agent import BaseAgent


class CodeGeneratorAgent(BaseAgent):
    """代码生成Agent

    根据需求生成Python代码。
    """

    SYSTEM_PROMPT = """你是一个专业的Python代码生成专家。

请根据用户需求生成高质量的Python代码，要求：
1. 遵循PEP 8规范
2. 添加类型注解
3. 包含docstring
4. 考虑异常处理

直接输出代码，使用```python代码块包裹。"""

    def __init__(self, llm: Any, tools: list[Any], memory: Optional[Any] = None) -> None:
        """初始化代码生成Agent

        Args:
            llm: LLM实例
            tools: 工具列表
            memory: 记忆系统实例
        """
        super().__init__(name="generator", llm=llm, tools=tools, memory=memory)

    def process(self, input_data: dict, context: dict) -> dict:
        """处理代码生成请求

        Args:
            input_data: 输入数据，包含requirement字段
            context: 共享上下文

        Returns:
            包含生成代码的结果字典
        """
        requirement = input_data.get("requirement", "")

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": f"请实现：{requirement}"},
        ]

        response = self.llm.invoke(messages)
        code = self._extract_code(response)

        return {
            "code": code,
            "raw_response": response,
            "requirement": requirement,
        }

    def _extract_code(self, response: str) -> str:
        """从响应中提取代码块

        Args:
            response: LLM响应文本

        Returns:
            提取的代码文本
        """
        # 匹配```python...```代码块
        pattern = r"```python\s*\n(.*?)\n```"
        matches = re.findall(pattern, response, re.DOTALL)
        if matches:
            return matches[0]

        # 匹配```...```代码块
        pattern = r"```\s*\n(.*?)\n```"
        matches = re.findall(pattern, response, re.DOTALL)
        if matches:
            return matches[0]

        # 如果没有代码块，返回原始响应
        return response.strip()
