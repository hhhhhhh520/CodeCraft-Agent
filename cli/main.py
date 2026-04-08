"""CLI主入口模块"""

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

    # 从环境变量获取API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        console.print("[red]Error: OPENAI_API_KEY environment variable not set[/red]")
        raise typer.Exit(1)

    # 创建LLM
    llm = LLMFactory.create("openai", "gpt-4o-mini", api_key=api_key)

    # 创建Agent
    from backend.agents import CodeGeneratorAgent

    generator = CodeGeneratorAgent(llm=llm, tools=[])

    # 创建Orchestrator
    agents = {"generator": generator}
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
        console.print("\n[bold green]生成的代码:[/bold green]\n")
        console.print(Markdown(f"```python\n{result['code']}\n```"))
    else:
        console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/red]")


@app.command()
def chat() -> None:
    """交互模式"""
    console.print(Panel("[bold green]CodeCraft Agent 交互模式[/bold green]"))
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
