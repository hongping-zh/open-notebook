"""CLI 主界面 - 使用 Typer 和 Rich 构建。"""

import typer
from typing import Optional
from rich.panel import Panel
from rich.text import Text
from acm_scholar_cli.config import config_app
from acm_scholar_cli.search import search_command, search_acm_command, interactive_command, last_command
from acm_scholar_cli.download import download_app
from acm_scholar_cli.library import library_app
from acm_scholar_cli.chat import chat_app
from acm_scholar_cli.data_cmd import data_app

app = typer.Typer(
    name="acm",
    help="ACM Scholar CLI - 在终端中搜索、下载论文并与AI对话",
    add_completion=False,
    pretty_exceptions_show_locals=False,
)

# 注册子命令
app.add_typer(config_app, name="config", help="管理 API 密钥和数据库凭据")
# app.add_typer(search_app, name="search", help="通过 OpenAlex 搜索 ACM 论文")
app.add_typer(download_app, name="download", help="下载论文 PDF 并建立索引")
app.add_typer(library_app, name="library", help="管理本地论文库")
app.add_typer(chat_app, name="chat", help="与论文进行 AI 对话")
app.add_typer(data_app, name="data", help="查看数据积累统计（数据壁垒）")

# 注册搜索命令
app.command(name="search", help="通过 OpenAlex 搜索论文")(search_command)
app.command(name="search-acm", help="专门搜索 ACM 出版物")(search_acm_command)
app.command(name="interactive", help="交互式搜索模式")(interactive_command)
app.command(name="last", help="显示上次搜索结果")(last_command)


def print_banner() -> None:
    """打印欢迎横幅。"""
    banner_text = Text()
    banner_text.append("ACM Scholar CLI", style="bold cyan")
    banner_text.append("\n")
    banner_text.append("在终端中搜索、下载论文并与AI对话", style="italic")
    banner_text.append("\n\n")
    banner_text.append("使用 ", style="dim")
    banner_text.append("acm --help", style="bold green")
    banner_text.append(" 查看所有命令", style="dim")

    panel = Panel(
        banner_text,
        title="[bold]ACM Scholar Agent[/bold]",
        subtitle="基于 OpenAlex 的学术研究工具",
        border_style="blue",
        padding=(1, 2),
    )
    typer.rich_utils.print_panel(panel)


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-v", help="显示版本号"),
) -> None:
    """
    ACM Scholar CLI 主回调函数。
    """
    if version:
        from acm_scholar_cli import __version__

        typer.echo(f"ACM Scholar CLI 版本: {__version__}")
        raise typer.Exit(0)

    # 如果没有子命令，打印欢迎信息
    if ctx.invoked_subcommand is None:
        print_banner()
        typer.echo("\n[dim]使用 acm --help 查看可用命令[/dim]")
