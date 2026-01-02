"""论文搜索模块 - 通过 OpenAlex API 搜索 ACM 论文。"""

from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.panel import Panel
from rich.prompt import Prompt
from rich import print as rprint
from acm_scholar_cli.core.searcher import Searcher
from acm_scholar_cli.config_manager import ConfigManager

search_app = typer.Typer(
    name="search",
    help="通过 OpenAlex 搜索 ACM 论文",
    add_completion=False,
)

console = Console()
config_manager = ConfigManager()
_last_search_results: list = []


def search_command(
    query: str = typer.Argument(..., help="搜索关键词"),
    year: Optional[int] = typer.Option(None, "--year", "-y", help="筛选特定年份的论文"),
    limit: int = typer.Option(10, "--limit", "-l", help="结果数量限制"),
    citations: Optional[int] = typer.Option(None, "--citations", "-c", help="最低引用数"),
) -> None:
    """
    搜索 ACM 论文。

    示例:
        acm search "Generative AI"
        acm search "Machine Learning" --year 2023 --limit 20
    """
    global _last_search_results

    config = config_manager.load()

    if not config:
        console.print("[bold red]请先运行 'acm config init' 进行配置[/bold red]")
        raise typer.Exit(1)

    searcher = Searcher(config)

    console.print(f"[cyan]正在搜索: '{query}'...[/cyan]")

    try:
        results = searcher.search(
            query=query,
            year=year,
            limit=limit,
            min_citations=citations,
        )

        _last_search_results = results

        if not results:
            console.print("[yellow]未找到相关论文[/yellow]")
            console.print("[dim]请尝试使用更通用的关键词[/dim]")
            return

        console.print(f"\n[bold green]找到 {len(results)} 篇论文[/bold green]\n")

        # 创建结果表格
        table = Table(title="搜索结果", show_header=True, header_style="bold magenta")
        table.add_column("#", width=4, style="dim")
        table.add_column("标题", width=50)
        table.add_column("作者", width=30)
        table.add_column("年份", width=6, justify="center")
        table.add_column("引用", width=8, justify="center")
        table.add_column("ID", width=20, style="dim")

        for idx, paper in enumerate(results, 1):
            # 截断过长的标题
            title = paper.get("title", "N/A")
            if len(title) > 48:
                title = title[:45] + "..."

            author_names = [a.get("author", {}).get("display_name", "") for a in paper.get("authorships", [])[:3]]
            authors = ", ".join([n for n in author_names if n])
            if len(authors) > 28:
                authors = authors[:25] + "..."

            year = str(paper.get("publication_year", "N/A"))
            citations = str(paper.get("cited_by_count", 0))
            paper_id = paper.get("id", "N/A").split("/")[-1]

            table.add_row(
                str(idx),
                title,
                authors,
                year,
                citations,
                paper_id,
            )

        console.print(table)

        # 提示用户可以执行的操作
        console.print("\n[dim]可以使用以下命令继续操作:[/dim]")
        console.print("  [green]acm download --paper-id <id>[/green] - 下载论文")
        console.print("  [green]acm search-interactive[/green] - 从上次搜索结果下载\n")

    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[bold red]搜索失败: {e}[/bold red]")
        raise typer.Exit(1)


def search_acm_command(
    query: str = typer.Argument(..., help="搜索关键词"),
    year: Optional[int] = typer.Option(None, "--year", "-y", help="筛选特定年份的论文"),
    limit: int = typer.Option(10, "--limit", "-l", help="结果数量限制"),
) -> None:
    """
    专门搜索 ACM 出版物中的论文。

    示例:
        acm search-acm "Neural Networks"
    """
    config = config_manager.load()

    if not config:
        console.print("[bold red]请先运行 'acm config init' 进行配置[/bold red]")
        raise typer.Exit(1)

    searcher = Searcher(config)

    console.print(f"[cyan]正在搜索 ACM 出版物: '{query}'...[/cyan]")

    try:
        results = searcher.search_acm(
            query=query,
            year=year,
            limit=limit,
        )

        if not results:
            console.print("[yellow]未找到 ACM 相关论文[/yellow]")
            raise typer.Exit(0)

        console.print(f"\n[bold green]找到 {len(results)} 篇 ACM 论文[/bold green]\n")

        # 创建结果表格
        table = Table(title="ACM 论文搜索结果", show_header=True, header_style="bold magenta")
        table.add_column("#", width=4, style="dim")
        table.add_column("标题", width=50)
        table.add_column("作者", width=30)
        table.add_column("年份", width=6, justify="center")
        table.add_column("引用", width=8, justify="center")

        for idx, paper in enumerate(results, 1):
            title = paper.get("title", "N/A")
            if len(title) > 48:
                title = title[:45] + "..."

            author_names = [a.get("author", {}).get("display_name", "") for a in paper.get("authorships", [])[:3]]
            authors = ", ".join([n for n in author_names if n])
            if len(authors) > 28:
                authors = authors[:25] + "..."

            year = str(paper.get("publication_year", "N/A"))
            citations = str(paper.get("cited_by_count", 0))

            table.add_row(str(idx), title, authors, year, citations)

        console.print(table)

    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[bold red]搜索失败: {e}[/bold red]")
        raise typer.Exit(1)


def interactive_command() -> None:
    """
    交互式搜索模式 - 可以在搜索结果中选择论文进行下载。
    """
    global _last_search_results

    if not _last_search_results:
        console.print("[bold yellow]请先执行搜索命令[/bold yellow]")
        raise typer.Exit(0)

    console.print("\n[bold cyan]从上次搜索结果中选择论文[/bold cyan]\n")

    # 显示论文列表
    table = Table(show_header=False)
    table.add_column("#", width=4)
    table.add_column("标题", width=60)

    for idx, paper in enumerate(_last_search_results, 1):
        title = paper.get("title", "N/A")
        if len(title) > 58:
            title = title[:55] + "..."
        table.add_row(str(idx), title)

    console.print(table)

    # 选择论文
    choice = Prompt.ask(
        "\n输入论文编号进行下载 (输入 'a' 下载全部, 'q' 退出)",
        choices=[str(i) for i in range(1, len(_last_search_results) + 1)] + ["a", "q"],
        default="q",
    )

    if choice == "q":
        console.print("已取消")
        raise typer.Exit(0)

    if choice == "a":
        paper_ids = [p.get("id", "").split("/")[-1] for p in _last_search_results]
        console.print(f"\n[cyan]将下载 {len(paper_ids)} 篇论文...[/cyan]")
    else:
        paper = _last_search_results[int(choice) - 1]
        paper_id = paper.get("id", "").split("/")[-1]
        console.print(f"\n[cyan]将下载论文: {paper_id}[/cyan]")


def last_command() -> None:
    """
    显示上次搜索的结果。
    """
    global _last_search_results

    if not _last_search_results:
        console.print("[bold yellow]没有搜索记录[/bold yellow]")
        raise typer.Exit(0)

    console.print(f"\n[bold]上次搜索结果 (共 {len(_last_search_results)} 篇)[/bold]\n")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", width=4)
    table.add_column("标题", width=60)
    table.add_column("年份", width=8)

    for idx, paper in enumerate(_last_search_results, 1):
        title = paper.get("title", "N/A")
        if len(title) > 58:
            title = title[:55] + "..."
        year = str(paper.get("publication_year", "N/A"))
        table.add_row(str(idx), title, year)

    console.print(table)
