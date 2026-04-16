"""调试Agent模块"""

import re
from typing import Any, Optional

from backend.core.agent import BaseAgent
from backend.tools.executor import CodeValidator


class DebuggerAgent(BaseAgent):
    """调试Agent

    分析错误并修复代码。
    """

    SYSTEM_PROMPT = """你是一个专业的Python调试专家。

根据提供的代码和问题列表，修复代码中的问题。

要求：
1. 保持原有功能不变
2. 修复所有列出的问题
3. 添加必要的错误处理
4. 保持代码风格一致

直接输出修复后的代码，使用```python代码块包裹。"""

    def __init__(self, llm: Any, tools: list[Any], memory: Optional[Any] = None, strict_security: bool = True) -> None:
        """初始化调试Agent

        Args:
            llm: LLM实例
            tools: 工具列表
            memory: 记忆系统实例
            strict_security: 是否启用严格安全验证
        """
        super().__init__(name="debugger", llm=llm, tools=tools, memory=memory)
        self.strict_security = strict_security

    def process(self, input_data: dict, context: dict) -> dict:
        """处理调试请求

        Args:
            input_data: 输入数据，包含code和issues字段
            context: 共享上下文

        Returns:
            包含修复后代码的结果字典
        """
        code = input_data.get("code", "")
        issues = input_data.get("issues", [])
        error_message = input_data.get("error_message", "")

        # 构建问题描述
        issues_text = "\n".join(
            [f"- [{i['severity']}] 行{i.get('line', '?')}: {i['message']}" for i in issues]
        )

        prompt = f"""请修复以下代码：

```python
{code}
```

问题列表：
{issues_text}

{f'错误信息：{error_message}' if error_message else ''}

请输出修复后的完整代码。"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        response = self.llm.invoke(messages)
        fixed_code = self._extract_code(response)

        # 安全验证
        security_issues = []
        if fixed_code:
            is_safe, sec_issues = CodeValidator.validate(fixed_code, strict=self.strict_security)
            if not is_safe:
                security_issues = sec_issues
                if self.strict_security:
                    return {
                        "fixed_code": code,  # 返回原始代码
                        "original_code": code,
                        "issues_fixed": 0,
                        "security_error": "修复后的代码未通过安全验证",
                        "security_issues": sec_issues,
                    }

        return {
            "fixed_code": fixed_code,
            "original_code": code,
            "issues_fixed": len(issues),
            "security_issues": security_issues,
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
