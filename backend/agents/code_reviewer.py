"""代码审查Agent模块"""

import json
import re
from typing import Any, Optional

from backend.core.agent import BaseAgent


class CodeReviewerAgent(BaseAgent):
    """代码审查Agent

    审查代码质量，发现问题并提出改进建议。
    """

    SYSTEM_PROMPT = """你是一个专业的Python代码审查专家。

请审查给定的代码，从以下维度评估：
1. 代码规范（PEP 8）
2. 潜在Bug
3. 性能问题
4. 安全隐患
5. 可维护性

以JSON格式返回审查结果：
{
    "passed": true/false,
    "issues": [
        {
            "severity": "high/medium/low",
            "type": "security/performance/style/bug",
            "line": 行号,
            "message": "问题描述",
            "suggestion": "改进建议"
        }
    ],
    "score": 0-100,
    "summary": "总体评价"
}

只返回JSON，不要其他内容。"""

    def __init__(self, llm: Any, tools: list[Any], memory: Optional[Any] = None) -> None:
        """初始化代码审查Agent

        Args:
            llm: LLM实例
            tools: 工具列表
            memory: 记忆系统实例
        """
        super().__init__(name="reviewer", llm=llm, tools=tools, memory=memory)

    def process(self, input_data: dict, context: dict) -> dict:
        """处理代码审查请求

        Args:
            input_data: 输入数据，包含code字段
            context: 共享上下文

        Returns:
            审查结果字典
        """
        code = input_data.get("code", "")

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": f"请审查以下代码：\n\n```python\n{code}\n```"},
        ]

        response = self.llm.invoke(messages)
        result = self._parse_response(response)

        return result

    def _parse_response(self, response: str) -> dict:
        """解析LLM响应

        Args:
            response: LLM响应文本

        Returns:
            解析后的审查结果
        """
        # 尝试提取JSON
        try:
            # 尝试直接解析
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # 尝试从代码块中提取
        json_pattern = r"```json\s*\n(.*?)\n```"
        matches = re.findall(json_pattern, response, re.DOTALL)
        if matches:
            try:
                return json.loads(matches[0])
            except json.JSONDecodeError:
                pass

        # 返回默认结果
        return {
            "passed": True,
            "issues": [],
            "score": 70,
            "summary": "无法解析审查结果",
            "raw_response": response,
        }
