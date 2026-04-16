"""输入验证工具模块"""

import re
from typing import Optional
from pydantic import BaseModel, Field, field_validator


# Prompt注入危险模式
PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+previous",
    r"ignore\s+all",
    r"system\s*prompt",
    r"<\|im_start\|>",
    r"<\|im_end\|>",
    r"you\s+are\s+now",
    r"forget\s+everything",
    r"disregard\s+",
    r"override\s+",
    r"jailbreak",
]


class UserRequirement(BaseModel):
    """用户需求验证模型"""
    requirement: str = Field(..., min_length=1, max_length=10000)

    @field_validator("requirement")
    @classmethod
    def sanitize(cls, v: str) -> str:
        """清理和验证输入"""
        # 移除控制字符
        v = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", v)

        # 检测潜在prompt injection
        for pattern in PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError(f"输入包含潜在的注入模式")

        return v.strip()


class APIKeyInput(BaseModel):
    """API Key验证模型"""
    api_key: str = Field(..., min_length=1, max_length=200)

    @field_validator("api_key")
    @classmethod
    def validate_format(cls, v: str) -> str:
        """验证API Key格式"""
        v = v.strip()

        # 检查基本格式
        if not v:
            raise ValueError("API Key不能为空")

        # 检查常见格式
        if v.startswith("sk-"):
            # OpenAI/DeepSeek格式
            if len(v) < 20:
                raise ValueError("API Key格式无效")
        elif v.startswith("sk-ant-"):
            # Anthropic格式
            if len(v) < 20:
                raise ValueError("API Key格式无效")
        else:
            # 其他格式，至少检查长度
            if len(v) < 10:
                raise ValueError("API Key格式无效")

        return v


def validate_requirement(requirement: str) -> tuple[bool, str, Optional[str]]:
    """验证用户需求输入

    Args:
        requirement: 用户输入的需求文本

    Returns:
        (是否有效, 清理后的文本, 错误消息)
    """
    if not requirement:
        return False, "", "需求不能为空"

    if len(requirement) > 10000:
        return False, "", "需求长度不能超过10000字符"

    try:
        validated = UserRequirement(requirement=requirement)
        return True, validated.requirement, None
    except ValueError as e:
        return False, "", str(e)


def validate_api_key(api_key: str) -> tuple[bool, str, Optional[str]]:
    """验证API Key输入

    Args:
        api_key: 用户输入的API Key

    Returns:
        (是否有效, 清理后的API Key, 错误消息)
    """
    if not api_key:
        return False, "", "API Key不能为空"

    try:
        validated = APIKeyInput(api_key=api_key)
        return True, validated.api_key, None
    except ValueError as e:
        return False, "", str(e)


def sanitize_for_display(text: str) -> str:
    """清理文本用于安全显示

    Args:
        text: 原始文本

    Returns:
        清理后的文本
    """
    # 移除控制字符
    text = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", text)
    # 限制长度
    if len(text) > 500:
        text = text[:500] + "..."
    return text
