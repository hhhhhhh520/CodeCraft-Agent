"""CLI主入口模块"""

import os
import sys

# 修复 Windows 控制台编码问题
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from typing import Any

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from backend.core import Orchestrator, SharedContext, Memory
from backend.llm import LLMFactory, TokenManager
from backend.tools import ASTParser, CodeExecutor
from backend.agents import (
    CodeGeneratorAgent,
    CodeReviewerAgent,
    DebuggerAgent,
    TestGeneratorAgent,
)

app = typer.Typer(
    name="codecraft",
    help="CodeCraft Agent - Multi-Agent Python code generation assistant",
)
console = Console()

# 全局 TokenManager 实例
_token_manager: TokenManager | None = None


def get_token_manager() -> TokenManager:
    """获取全局 TokenManager 实例"""
    global _token_manager
    if _token_manager is None:
        _token_manager = TokenManager(max_tokens=128000)
    return _token_manager


def get_orchestrator(fast: bool = False) -> Orchestrator:
    """获取Orchestrator实例

    Args:
        fast: 快速模式，跳过代码审查和测试生成

    Returns:
        配置好的Orchestrator实例
    """
    # 支持 DeepSeek 或 OpenAI
    api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        console.print("[red]Error: 请设置 DEEPSEEK_API_KEY 或 OPENAI_API_KEY 环境变量[/red]")
        raise typer.Exit(1)

    # 判断使用哪个API
    if os.getenv("DEEPSEEK_API_KEY"):
        base_url = "https://api.deepseek.com/v1"
        model = "deepseek-chat"
        console.print("[dim]使用 DeepSeek API[/dim]")
    else:
        base_url = None
        model = "gpt-4o-mini"
        console.print("[dim]使用 OpenAI API[/dim]")

    # 创建LLM（集成 TokenManager）
    token_manager = get_token_manager()
    llm = LLMFactory.create("openai", model, api_key=api_key, base_url=base_url, token_manager=token_manager)

    # 创建工具
    tools: list[Any] = [ASTParser(), CodeExecutor(timeout=30)]

    # 创建记忆系统
    memory = Memory(enable_vector=True)

    # 创建所有Agent（注入 tools 和 memory）
    generator = CodeGeneratorAgent(llm=llm, tools=tools, memory=memory)
    agents: dict[str, Any] = {"generator": generator}

    if not fast:
        reviewer = CodeReviewerAgent(llm=llm, tools=tools, memory=memory)
        debugger = DebuggerAgent(llm=llm, tools=tools, memory=memory)
        test_generator = TestGeneratorAgent(llm=llm, tools=tools, memory=memory)
        agents["reviewer"] = reviewer
        agents["debugger"] = debugger
        agents["test_generator"] = test_generator

    # 创建Orchestrator
    context = SharedContext()

    return Orchestrator(agents=agents, context=context)


@app.command()
def generate(requirement: str, fast: bool = False) -> None:
    """生成代码

    Args:
        requirement: 代码需求描述
        fast: 快速模式，跳过代码审查
    """
    console.print(Panel(f"[bold blue]正在生成代码...[/bold blue]\n{requirement}"))

    orchestrator = get_orchestrator(fast=fast)

    if fast:
        console.print("[dim]快速模式：跳过代码审查[/dim]")

    result = orchestrator.process_request(requirement)

    if "code" in result:
        # 显示审查结果
        if not fast and "review_score" in result:
            score = result["review_score"]
            if score >= 90:
                console.print(f"\n[bold green]✓ 代码审查通过[/bold green] (评分: {score})")
            else:
                console.print(f"\n[bold yellow]⚠ 代码已自动修复优化[/bold yellow] (评分: {score} → 优化后)")

        console.print("\n[bold green]生成的代码:[/bold green]\n")
        console.print(Markdown(f"```python\n{result['code']}\n```"))
    else:
        console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/red]")


@app.command()
def chat(fast: bool = False) -> None:
    """交互模式

    Args:
        fast: 快速模式，跳过代码审查
    """
    console.print(Panel("[bold green]CodeCraft Agent 交互模式[/bold green]"))
    if fast:
        console.print("[dim]快速模式：跳过代码审查[/dim]")
    else:
        console.print("多Agent协作: 生成 → 审查 → 修复优化 → 测试")
    console.print("输入需求生成代码，输入 'exit' 退出\n")

    orchestrator = get_orchestrator(fast=fast)

    # 显示 Token 使用情况
    token_manager = get_token_manager()

    while True:
        try:
            user_input = console.input("[bold blue]You:[/bold blue] ")
            if user_input.lower() == "exit":
                console.print("[green]再见！[/green]")
                break

            result = orchestrator.process_request(user_input)

            if "code" in result:
                # 显示审查结果
                if not fast and "review_score" in result:
                    score = result["review_score"]
                    if score >= 90:
                        console.print(f"\n[bold green]✓ 代码审查通过[/bold green] (评分: {score})")
                    else:
                        console.print(f"\n[bold yellow]⚠ 代码已自动修复优化[/bold yellow]")

                console.print("\n[bold green]CodeCraft:[/bold green]\n")
                console.print(Markdown(f"```python\n{result['code']}\n```"))
            else:
                console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/red]")

        except KeyboardInterrupt:
            console.print("\n[green]再见！[/green]")
            break


@app.command()
def version() -> None:
    """显示版本信息"""
    from backend import __version__

    console.print(f"CodeCraft Agent v{__version__}")


if __name__ == "__main__":
    app()
