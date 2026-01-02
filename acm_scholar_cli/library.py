"""文库管理模块 - 管理本地下载的论文。"""

from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.text import Text
from datetime import datetime
from acm_scholar_cli.config_manager import ConfigManager

library_app = typer.Typer(
    name="library",
    help="管理本地论文库",
    add_completion=False,
)

console = Console()
config_manager = ConfigManager()


@library_app.command("list")
def library_list(
    limit: int = typer.Option(20, "--limit", "-l", help="显示数量限制"),
    sort_by: str = typer.Option("date", "--sort", "-s", help="排序方式 (date, title, citations)"),
) -> None:
    """
    列出本地下载的论文。

    示例:
        acm library list
        acm library list --limit 50 --sort citations
    """
    download_dir = config_manager.get_download_dir()

    if not download_dir.exists():
        console.print("[bold yellow]论文库为空，尚未下载任何论文[/bold yellow]")
        raise typer.Exit(0)

    # 扫描下载目录
    pdf_files = list(download_dir.glob("*.pdf"))

    if not pdf_files:
        console.print("[bold yellow]论文库为空[/bold yellow]")
        raise typer.Exit(0)

    # 获取文件信息
    papers = []
    for pdf_file in pdf_files:
        stat = pdf_file.stat()
        papers.append({
            "file": pdf_file,
            "name": pdf_file.name,
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime),
        })

    # 排序
    if sort_by == "title":
        papers.sort(key=lambda x: x["name"])
    elif sort_by == "size":
        papers.sort(key=lambda x: x["size"], reverse=True)
    else:  # date
        papers.sort(key=lambda x: x["modified"], reverse=True)

    # 限制数量
    papers = papers[:limit]

    console.print(f"\n[bold]本地论文库 (共 {len(pdf_files)} 篇)[/bold]\n")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", width=4, style="dim")
    table.add_column("文件名", width=50)
    table.add_column("大小", width=12, justify="right")
    table.add_column("修改日期", width=20)

    for idx, paper in enumerate(papers, 1):
        size_str = _format_size(paper["size"])
        date_str = paper["modified"].strftime("%Y-%m-%d %H:%M")

        # 截断过长的文件名
        name = paper["name"]
        if len(name) > 48:
            name = name[:45] + "..."

        table.add_row(str(idx), name, size_str, date_str)

    console.print(table)


@library_app.command("stats")
def library_stats() -> None:
    """
    显示论文库统计信息。
    """
    download_dir = config_manager.get_download_dir()

    if not download_dir.exists():
        console.print("[bold yellow]论文库为空[/bold yellow]")
        raise typer.Exit(0)

    pdf_files = list(download_dir.glob("*.pdf"))

    total_size = sum(f.stat().st_size for f in pdf_files)

    table = Table(title="论文库统计", show_header=False)
    table.add_column("项目", style="cyan")
    table.add_column("值", style="green")

    table.add_row("论文总数", str(len(pdf_files)))
    table.add_row("总大小", _format_size(total_size))
    table.add_row("存储位置", str(download_dir))

    console.print(table)


@library_app.command("remove")
def library_remove(
    paper_id: str = typer.Argument(..., help="论文文件名或编号"),
    force: bool = typer.Option(False, "--force", "-f", help="强制删除，不确认"),
) -> None:
    """
    从论文库中删除论文。

    示例:
        acm library remove "author_2023_paper.pdf"
        acm library remove 1 --force
    """
    download_dir = config_manager.get_download_dir()

    if not download_dir.exists():
        console.print("[bold yellow]论文库为空[/bold yellow]")
        raise typer.Exit(0)

    pdf_files = {f: f for f in download_dir.glob("*.pdf")}

    # 检查是否是数字编号
    if paper_id.isdigit():
        idx = int(paper_id)
        if 1 <= idx <= len(pdf_files):
            pdf_file = list(pdf_files.keys())[idx - 1]
        else:
            console.print(f"[bold red]无效的编号: {paper_id}[/bold red]")
            raise typer.Exit(1)
    else:
        # 按文件名匹配
        pdf_file = download_dir / paper_id
        if not pdf_file.exists():
            console.print(f"[bold red]文件不存在: {paper_id}[/bold red]")
            raise typer.Exit(1)

    # 确认删除
    if not force:
        confirm = typer.confirm(f"确定要删除 {pdf_file.name} 吗?")
        if not confirm:
            console.print("已取消")
            raise typer.Exit(0)

    try:
        pdf_file.unlink()
        console.print(f"[bold green]✓ 已删除: {pdf_file.name}[/bold green]")
    except Exception as e:
        console.print(f"[bold red]删除失败: {e}[/bold red]")
        raise typer.Exit(1)


@library_app.command("clean")
def library_clean(
    older_than: Optional[int] = typer.Option(None, "--older-than", "-d", help="删除多少天前的文件"),
    empty: bool = typer.Option(False, "--empty", help="清空整个论文库"),
) -> None:
    """
    清理论文库。

    示例:
        acm library clean --older-than 30  # 删除30天前的文件
        acm library clean --empty  # 清空整个论文库
    """
    download_dir = config_manager.get_download_dir()

    if not download_dir.exists():
        console.print("[bold yellow]论文库为空[/bold yellow]")
        raise typer.Exit(0)

    if empty:
        confirm = typer.confirm("确定要清空整个论文库吗? 此操作不可恢复!")
        if not confirm:
            console.print("已取消")
            raise typer.Exit(0)

        # 删除所有 PDF 文件
        pdf_files = list(download_dir.glob("*.pdf"))
        count = 0
        for pdf_file in pdf_files:
            try:
                pdf_file.unlink()
                count += 1
            except Exception as e:
                console.print(f"[red]删除失败: {pdf_file.name} - {e}[/red]")

        console.print(f"[bold green]✓ 已清空论文库，删除了 {count} 个文件[/bold green]")
        return

    if older_than:
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=older_than)
        pdf_files = list(download_dir.glob("*.pdf"))

        count = 0
        for pdf_file in pdf_files:
            if pdf_file.stat().st_mtime < cutoff_date.timestamp():
                try:
                    pdf_file.unlink()
                    count += 1
                except Exception as e:
                    console.print(f"[red]删除失败: {pdf_file.name} - {e}[/red]")

        console.print(f"[bold green]✓ 已删除 {count} 个旧文件[/bold green]")
        return

    console.print("[bold yellow]请指定 --older-than 或 --empty 参数[/bold yellow]")


@library_app.command("search")
def library_search(
    keyword: str = typer.Argument(..., help="搜索关键词"),
) -> None:
    """
    在本地论文库中搜索。

    示例:
        acm library search "neural"
    """
    download_dir = config_manager.get_download_dir()

    if not download_dir.exists():
        console.print("[bold yellow]论文库为空[/bold yellow]")
        raise typer.Exit(0)

    pdf_files = list(download_dir.glob("*.pdf"))
    keyword = keyword.lower()

    # 按文件名搜索
    matching = [
        f for f in pdf_files
        if keyword in f.name.lower()
    ]

    if not matching:
        console.print(f"[yellow]未找到包含 '{keyword}' 的论文[/yellow]")
        raise typer.Exit(0)

    console.print(f"\n[bold]找到 {len(matching)} 篇匹配论文[/bold]\n")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", width=4)
    table.add_column("文件名", width=60)

    for idx, pdf_file in enumerate(matching, 1):
        name = pdf_file.name
        if len(name) > 58:
            name = name[:55] + "..."
        table.add_row(str(idx), name)

    console.print(table)


def _format_size(size_bytes: int) -> str:
    """
    格式化文件大小。

    Args:
        size_bytes: 字节大小

    Returns:
        格式化后的大小字符串
    """
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"
