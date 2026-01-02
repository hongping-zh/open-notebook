"""配置管理模块。"""

import os
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from acm_scholar_cli.config_manager import ConfigManager, Config

config_app = typer.Typer(
    name="config",
    help="管理 API 密钥和数据库凭据",
    add_completion=False,
)

console = Console()
config_manager = ConfigManager()


@config_app.command("init")
def config_init() -> None:
    """
    交互式配置向导。
    """
    console.print("[bold cyan]ACM Scholar CLI 配置向导[/bold cyan]\n")

    # 加载现有配置或创建新的
    config = config_manager.load() or Config()

    # OpenAlex 配置
    console.print("[yellow]OpenAlex 配置[/yellow]")
    email = Prompt.ask(
        "请输入您的邮箱 (用于 OpenAlex polite pool)",
        default=config.openalex.email or "",
    )
    config.openalex.email = email

    # LLM 配置
    console.print("\n[yellow]LLM 配置[/yellow]")
    providers = ["openai", "deepseek", "ollama"]
    provider = Prompt.ask(
        "选择 LLM 提供商",
        choices=providers,
        default=config.llm.provider or "openai",
    )
    config.llm.provider = provider

    if provider in ["openai", "deepseek"]:
        api_key = Prompt.ask(
            f"请输入 {provider} API Key",
            password=True,
            default=config.llm.api_key or "",
        )
        config.llm.api_key = api_key

        model = Prompt.ask(
            f"请输入模型名称",
            default=config.llm.model or ("gpt-4" if provider == "openai" else "deepseek-chat"),
        )
        config.llm.model = model

    # 数据库配置
    console.print("\n[yellow]SurrealDB 配置 (可选)[/yellow]")
    use_db = Prompt.ask(
        "是否使用 SurrealDB?",
        choices=["y", "n"],
        default="y" if config.database.host else "n",
    )

    if use_db == "y":
        host = Prompt.ask(
            "SurrealDB 主机",
            default=config.database.host or "localhost",
        )
        config.database.host = host

        port = Prompt.ask(
            "SurrealDB 端口",
            default=str(config.database.port or 8000),
        )
        config.database.port = int(port)

        user = Prompt.ask(
            "用户名",
            default=config.database.user or "root",
        )
        config.database.user = user

        password = Prompt.ask(
            "密码",
            password=True,
            default=config.database.password or "",
        )
        config.database.password = password

    # 下载目录
    console.print("\n[yellow]下载设置[/yellow]")
    download_dir = Prompt.ask(
        "论文下载目录",
        default=config.download.directory or "~/acm-papers/",
    )
    config.download.directory = download_dir

    # 保存配置
    config_manager.save(config)
    console.print("\n[bold green]✓ 配置已保存![/bold green]")
    console.print(f"配置文件位置: {config_manager.config_path}")


@config_app.command("show")
def config_show() -> None:
    """
    显示当前配置。
    """
    config = config_manager.load()

    if not config:
        console.print("[bold red]配置不存在，请先运行 'acm config init'[/bold red]")
        raise typer.Exit(1)

    table = Table(title="当前配置")
    table.add_column("配置项", style="cyan")
    table.add_column("值", style="green")

    table.add_row("OpenAlex 邮箱", config.openalex.email or "未设置")
    table.add_row("LLM 提供商", config.llm.provider or "未设置")
    table.add_row("LLM 模型", config.llm.model or "未设置")
    table.add_row("数据库主机", config.database.host or "未设置")
    table.add_row("数据库端口", str(config.database.port or "未设置"))
    table.add_row("下载目录", config.download.directory or "未设置")

    console.print(table)


@config_app.command("set")
def config_set(
    key: str = typer.Argument(..., help="配置项名称"),
    value: str = typer.Argument(..., help="配置值"),
) -> None:
    """
    设置配置项。
    """
    valid_keys = [
        "openalex.email",
        "llm.provider",
        "llm.api_key",
        "llm.model",
        "database.host",
        "database.port",
        "database.user",
        "database.password",
        "download.directory",
    ]

    if key not in valid_keys:
        console.print(f"[bold red]无效的配置项: {key}[/bold red]")
        console.print(f"有效配置项: {', '.join(valid_keys)}")
        raise typer.Exit(1)

    config = config_manager.load() or Config()

    # 更新配置
    parts = key.split(".")
    if len(parts) == 2:
        setattr(
            getattr(config, parts[0]),
            parts[1],
            value,
        )

    config_manager.save(config)
    console.print(f"[bold green]✓ 已设置 {key} = {value}[/bold green]")


@config_app.command("check")
def config_check() -> None:
    """
    检查配置是否有效。
    """
    config = config_manager.load()

    if not config:
        console.print("[bold red]配置不存在，请先运行 'acm config init'[/bold red]")
        raise typer.Exit(1)

    table = Table(title="配置检查")
    table.add_column("检查项", style="cyan")
    table.add_column("状态", style="green")

    # 检查 OpenAlex
    if config.openalex.email:
        table.add_row("OpenAlex 邮箱", "[green]✓ 已配置[/green]")
    else:
        table.add_row("OpenAlex 邮箱", "[red]✗ 未配置[/red]")

    # 检查 LLM
    if config.llm.api_key or config.llm.provider == "ollama":
        table.add_row("LLM API Key", "[green]✓ 已配置[/green]")
    else:
        table.add_row("LLM API Key", "[yellow]⚠ 未配置 (将使用本地模型)[/yellow]")

    # 检查数据库
    if config.database.host:
        table.add_row("SurrealDB", "[green]✓ 已配置[/green]")
    else:
        table.add_row("SurrealDB", "[yellow]⚠ 未配置 (将使用内存存储)[/yellow]")

    # 检查下载目录
    download_dir = Path(config.download.directory or "~/acm-papers/").expanduser()
    if download_dir.exists():
        table.add_row("下载目录", "[green]✓ 存在[/green]")
    else:
        table.add_row("下载目录", f"[yellow]⚠ 将创建: {download_dir}[/yellow]")

    console.print(table)
