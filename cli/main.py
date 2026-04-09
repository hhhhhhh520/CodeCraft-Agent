"""CLI主入口模块"""

import os
import sys

# 修复 Windows 控制台编码问题
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from backend.core import Orchestrator, SharedContext
from backend.llm import LLMFactory

app = typer.Typer(
    name="codecraft",
    help="CodeCraft Agent - Multi-Agent Python code generation assistant",
)
console = Console()


def get_orchestrator() -> Orchestrator:
    """获取Orchestrator实例

    Returns:
        配置好的Orchestrator实例
    """
    import os

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

    # 创建LLM
    llm = LLMFactory.create("openai", model, api_key=api_key, base_url=base_url)

    # 创建所有Agent
    from backend.agents import (
        CodeGeneratorAgent,
        CodeReviewerAgent,
        DebuggerAgent,
    )

    generator = CodeGeneratorAgent(llm=llm, tools=[])
    reviewer = CodeReviewerAgent(llm=llm, tools=[])
    debugger = DebuggerAgent(llm=llm, tools=[])

    # 创建Orchestrator（完整多Agent协作）
    agents = {
        "generator": generator,
        "reviewer": reviewer,
        "debugger": debugger,
    }
    context = SharedContext()

    return Orchestrator(agents=agents, context=context)


@app.command()
def generate(requirement: str) -> None:
    """生成代码

    Args:
        requirement: 代码需求描述
    """
    console.print(Panel(f"[bold blue]正在生成代码...[/bold blue]\n{requirement}"))

    orchestrator = get_orchestrator()
    result = orchestrator.process_request(requirement)

    if "code" in result:
        # 显示审查结果
        if "review_score" in result:
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
def chat() -> None:
    """交互模式"""
    console.print(Panel("[bold green]CodeCraft Agent 交互模式[/bold green]"))
    console.print("多Agent协作: 生成 → 审查 → 修复优化")
    console.print("输入需求生成代码，输入 'exit' 退出\n")

    orchestrator = get_orchestrator()

    while True:
        try:
            user_input = console.input("[bold blue]You:[/bold blue] ")
            if user_input.lower() == "exit":
                console.print("[green]再见！[/green]")
                break

            result = orchestrator.process_request(user_input)

            if "code" in result:
                # 显示审查结果
                if "review_score" in result:
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
