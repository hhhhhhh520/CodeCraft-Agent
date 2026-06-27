"""代码生成Agent模块"""

from typing import Any, Optional

from backend.core.agent import BaseAgent
from backend.tools.executor import CodeValidator
from backend.utils.code_utils import extract_code_from_response


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

安全约束（必须遵守）：
- 禁止使用 importlib、runpy、ctypes 等动态导入/执行模块
- 禁止使用 eval()、exec()、compile()、__import__()
- 禁止通过 __class__、__bases__、__subclasses__、__mro__ 等魔术属性进行反射
- 需要导入模块时使用标准 import 语句，不要动态导入

直接输出代码，使用```python代码块包裹。"""

    def __init__(self, llm: Any, tools: list[Any], memory: Optional[Any] = None, strict_security: bool = True) -> None:
        """初始化代码生成Agent

        Args:
            llm: LLM实例
            tools: 工具列表
            memory: 记忆系统实例
            strict_security: 是否启用严格安全验证
        """
        super().__init__(name="generator", llm=llm, tools=tools, memory=memory)
        self.strict_security = strict_security

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
        code = extract_code_from_response(response)

        # 安全验证
        security_issues = []
        if code:
            is_safe, issues = CodeValidator.validate(code, strict=self.strict_security)
            if not is_safe:
                security_issues = issues
                if self.strict_security:
                    return {
                        "code": "",
                        "raw_response": response,
                        "requirement": requirement,
                        "security_error": "生成的代码未通过安全验证",
                        "security_issues": issues,
                    }

        return {
            "code": code,
            "raw_response": response,
            "requirement": requirement,
            "security_issues": security_issues,
        }

