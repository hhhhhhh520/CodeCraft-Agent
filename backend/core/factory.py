"""Orchestrator 装配工厂模块

统一 CLI 与 Streamlit 两个入口的 Orchestrator 组装逻辑，
配置来源（环境变量 / 会话配置）由调用方决定。
"""

from typing import Any, Optional

from .context import SharedContext
from .orchestrator import Orchestrator
from ..agents import (
    CodeGeneratorAgent,
    CodeReviewerAgent,
    DebuggerAgent,
    TestGeneratorAgent,
)
from ..llm import LLMFactory, TokenManager
from ..tools import ASTParser, CodeExecutor


def create_orchestrator(
    api_key: str,
    model: str,
    base_url: Optional[str] = None,
    fast: bool = False,
    token_manager: Optional[TokenManager] = None,
) -> Orchestrator:
    """按统一流程装配 Orchestrator

    Args:
        api_key: LLM API Key（来源由调用方决定：CLI 读环境变量，Web 读会话配置）
        model: 模型名
        base_url: OpenAI 兼容端点，None 表示 OpenAI 官方
        fast: 快速模式，只注册 generator
        token_manager: Token 统计器，None 则新建

    Returns:
        配置好的 Orchestrator 实例
    """
    if token_manager is None:
        token_manager = TokenManager(max_tokens=128000)
    llm = LLMFactory.create(
        "openai", model, api_key=api_key, base_url=base_url, token_manager=token_manager
    )

    tools: list[Any] = [ASTParser(), CodeExecutor(timeout=30)]
    agents: dict[str, Any] = {"generator": CodeGeneratorAgent(llm=llm, tools=tools)}
    if not fast:
        agents["reviewer"] = CodeReviewerAgent(llm=llm, tools=tools)
        agents["debugger"] = DebuggerAgent(llm=llm, tools=tools)
        agents["test_generator"] = TestGeneratorAgent(llm=llm, tools=tools)

    return Orchestrator(agents=agents, context=SharedContext())
