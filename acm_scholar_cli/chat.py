"""AI 对话模块 - 与论文进行 AI 对话。"""

from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown
from rich.prompt import Prompt
from acm_scholar_cli.config_manager import ConfigManager
from acm_scholar_cli.core.chat_engine import ChatEngine

chat_app = typer.Typer(
    name="chat",
    help="与论文进行 AI 对话",
    add_completion=False,
)

console = Console()
config_manager = ConfigManager()


@chat_app.command("default")
def chat_paper(
    paper_id: Optional[str] = typer.Argument(None, help="论文 ID (OpenAlex ID)"),
    global_chat: bool = typer.Option(False, "--global", "-g", help="在整个文库中对话"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="指定使用的模型"),
    stream: bool = typer.Option(True, "--stream/--no-stream", help="流式输出"),
) -> None:
    """
    与论文进行 AI 对话。

    示例:
        acm chat W1234567890
        acm chat --global
        acm chat W1234567890 --model gpt-4
    """
    config = config_manager.load()

    if not config:
        console.print("[bold red]请先运行 'acm config init' 进行配置[/bold red]")
        raise typer.Exit(1)

    if not config.llm.api_key and config.llm.provider != "ollama":
        console.print("[bold yellow]请配置 LLM API Key 以使用对话功能[/bold yellow]")
        console.print("运行 'acm config init' 进行配置")
        raise typer.Exit(1)

    # 初始化聊天引擎
    chat_engine = ChatEngine(config)

    if global_chat:
        console.print("[cyan]进入全局对话模式 - 将在整个文库中搜索[/cyan]")
        chat_engine.set_mode("global")
    elif paper_id:
        console.print(f"[cyan]加载论文: {paper_id}[/cyan]")
        chat_engine.load_paper(paper_id)
    else:
        console.print("[bold red]请指定论文 ID 或使用 --global 模式[/bold red]")
        raise typer.Exit(1)

    # 设置模型
    if model:
        chat_engine.set_model(model)

    # 进入交互式对话
    _start_interactive_chat(chat_engine)


@chat_app.command("interactive")
def chat_interactive(
    global_chat: bool = typer.Option(False, "--global", "-g", help="在整个文库中对话"),
) -> None:
    """
    交互式对话模式 - 无需指定论文即可开始对话。

    示例:
        acm chat interactive
        acm chat interactive --global
    """
    config = config_manager.load()

    if not config:
        console.print("[bold red]请先运行 'acm config init' 进行配置[/bold red]")
        raise typer.Exit(1)

    chat_engine = ChatEngine(config)

    if global_chat:
        console.print("[cyan]进入全局对话模式[/cyan]")
        chat_engine.set_mode("global")
    else:
        console.print("[cyan]进入交互式对话模式[/cyan]")
        console.print("[dim]使用 /paper <id> 加载特定论文[/dim]")
        console.print("[dim]使用 /global 切换到全局模式[/dim]")
        console.print("[dim]使用 /exit 退出[/dim]\n")

    _start_interactive_chat(chat_engine)


def _start_interactive_chat(chat_engine: ChatEngine) -> None:
    """
    启动交互式对话循环。

    Args:
        chat_engine: 聊天引擎实例
    """
    welcome_text = Text()
    welcome_text.append("AI 对话已启动\n", style="bold green")
    welcome_text.append("输入问题与论文对话\n", style="dim")
    welcome_text.append("命令: ", style="dim")
    welcome_text.append("/exit ", style="cyan")
    welcome_text.append("- 退出, ", style="dim")
    welcome_text.append("/clear ", style="cyan")
    welcome_text.append("- 清屏, ", style="dim")
    welcome_text.append("/source ", style="cyan")
    welcome_text.append("- 显示引用来源", style="dim")

    panel = Panel(
        welcome_text,
        title="[bold]AI Chat[/bold]",
        border_style="green",
    )
    console.print(panel)

    while True:
        try:
            user_input = Prompt.ask("\n[bold you[/bold]")

            if not user_input.strip():
                continue

            # 检查特殊命令
            if user_input.lower() in ["/exit", "/quit", "/q"]:
                console.print("[bold yellow]再见![/bold yellow]")
                break

            if user_input.lower() == "/clear":
                console.clear()
                continue

            if user_input.lower() == "/source":
                sources = chat_engine.get_last_sources()
                if sources:
                    console.print("\n[bold cyan]引用来源:[/bold cyan]")
                    for source in sources:
                        console.print(f"  - {source}")
                else:
                    console.print("[yellow]没有可用的引用来源[/yellow]")
                continue

            if user_input.startswith("/paper "):
                paper_id = user_input[7:].strip()
                if paper_id:
                    chat_engine.load_paper(paper_id)
                    console.print(f"[green]已加载论文: {paper_id}[/green]")
                else:
                    console.print("[yellow]请指定论文 ID[/yellow]")
                continue

            if user_input.lower() == "/global":
                chat_engine.set_mode("global")
                console.print("[green]已切换到全局模式[/green]")
                continue

            # 正常对话
            console.print("\n[cyan]思考中...[/cyan]")

            response = chat_engine.chat(user_input)

            if response:
                console.print("\n[bold green]AI:[/bold green]")
                console.print(Markdown(response))

        except KeyboardInterrupt:
            console.print("\n[bold yellow]再见![/bold yellow]")
            break
        except Exception as e:
            console.print(f"[bold red]错误: {e}[/bold red]")


@chat_app.command("ask")
def chat_ask(
    question: str = typer.Argument(..., help="要问的问题"),
    paper_id: Optional[str] = typer.Option(None, "--paper", "-p", help="论文 ID"),
    global_chat: bool = typer.Option(False, "--global", "-g", help="在整个文库中搜索"),
) -> None:
    """
    直接问一个问题（非交互式）。

    示例:
        acm chat ask "这篇论文的主要贡献是什么?"
        acm chat ask "总结论文的核心观点" --paper W1234567890
    """
    config = config_manager.load()

    if not config:
        console.print("[bold red]请先运行 'acm config init' 进行配置[/bold red]")
        raise typer.Exit(1)

    chat_engine = ChatEngine(config)

    if global_chat:
        chat_engine.set_mode("global")
    elif paper_id:
        chat_engine.load_paper(paper_id)

    try:
        response = chat_engine.chat(question)

        if response:
            console.print("\n[bold green]回答:[/bold green]")
            console.print(Markdown(response))

        # 显示来源
        sources = chat_engine.get_last_sources()
        if sources:
            console.print("\n[bold cyan]引用来源:[/bold cyan]")
            for source in sources:
                console.print(f"  - {source}")

    except Exception as e:
        console.print(f"[bold red]错误: {e}[/bold red]")
        raise typer.Exit(1)


@chat_app.command("summarize")
def chat_summarize(
    paper_id: str = typer.Argument(..., help="论文 ID"),
    length: str = typer.Option("medium", "--length", "-l", help="总结长度 (short, medium, long)"),
) -> None:
    """
    对论文进行总结。

    示例:
        acm chat summarize W1234567890
        acm chat summarize W1234567890 --length short
    """
    config = config_manager.load()

    if not config:
        console.print("[bold red]请先运行 'acm config init' 进行配置[/bold red]")
        raise typer.Exit(1)

    chat_engine = ChatEngine(config)
    chat_engine.load_paper(paper_id)

    try:
        console.print(f"[cyan]正在总结论文...[/cyan]")

        summary = chat_engine.summarize(length=length)

        if summary:
            console.print("\n[bold green]论文总结:[/bold green]")
            console.print(Markdown(summary))

    except Exception as e:
        console.print(f"[bold red]错误: {e}[/bold red]")
        raise typer.Exit(1)
