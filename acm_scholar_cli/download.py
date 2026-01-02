"""论文下载模块。"""

from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, DownloadColumn, TimeElapsedColumn
from rich.prompt import Prompt
from acm_scholar_cli.core.searcher import Searcher
from acm_scholar_cli.core.downloader import PaperDownloader
from acm_scholar_cli.config_manager import ConfigManager

download_app = typer.Typer(
    name="download",
    help="下载论文 PDF 并建立索引",
    add_completion=False,
)

console = Console()
config_manager = ConfigManager()


@download_app.command("default")
def download_paper(
    paper_id: str = typer.Argument(..., help="论文 ID (OpenAlex ID)"),
    index: bool = typer.Option(True, "--index/--no-index", help="是否建立向量索引"),
) -> None:
    """
    下载论文 PDF。

    示例:
        acm download W1234567890
        acm download W1234567890 --no-index
    """
    config = config_manager.load()

    if not config:
        console.print("[bold red]请先运行 'acm config init' 进行配置[/bold red]")
        raise typer.Exit(1)

    searcher = Searcher(config)
    downloader = PaperDownloader(config)

    console.print(f"[cyan]正在获取论文信息: {paper_id}[/cyan]")

    # 获取论文详情
    paper = searcher.get_paper_by_id(paper_id)

    if not paper:
        console.print(f"[bold red]未找到论文: {paper_id}[/bold red]")
        raise typer.Exit(1)

    title = paper.get("title", "Unknown")
    console.print(f"[cyan]论文标题: {title}[/cyan]")

    # 获取 PDF URL
    pdf_url = searcher.get_pdf_url(paper)

    if not pdf_url:
        console.print("[bold red]无法找到该论文的 PDF 下载链接[/bold red]")
        console.print("[yellow]该论文可能不在开放获取范围内[/yellow]")
        raise typer.Exit(1)

    # 下载论文
    console.print(f"[cyan]正在下载 PDF...[/cyan]")

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TextColumn("({time_elapsed})"),
            console=console,
        ) as progress:
            file_path = downloader.download_pdf(
                paper=paper,
                url=pdf_url,
                progress=progress,
            )

        console.print(f"\n[bold green]✓ 论文已下载到: {file_path}[/bold green]")

        # 建立索引
        if index:
            console.print("[cyan]正在建立索引...[/cyan]")
            downloader.index_paper(paper, file_path)
            console.print("[bold green]✓ 索引建立完成[/bold green]")

    except Exception as e:
        console.print(f"[bold red]下载失败: {e}[/bold red]")
        raise typer.Exit(1)


@download_app.command("batch")
def download_batch(
    file_path: Path = typer.Argument(..., help="包含论文 ID 的文件路径 (每行一个 ID)"),
    index: bool = typer.Option(True, "--index/--no-index", help="是否建立向量索引"),
) -> None:
    """
    批量下载论文。

    示例:
        acm download batch ids.txt
        acm download batch ids.txt --no-index
    """
    config = config_manager.load()

    if not config:
        console.print("[bold red]请先运行 'acm config init' 进行配置[/bold red]")
        raise typer.Exit(1)

    if not file_path.exists():
        console.print(f"[bold red]文件不存在: {file_path}[/bold red]")
        raise typer.Exit(1)

    # 读取论文 ID
    with open(file_path, "r", encoding="utf-8") as f:
        paper_ids = [line.strip() for line in f if line.strip()]

    if not paper_ids:
        console.print("[bold red]文件中没有论文 ID[/bold red]")
        raise typer.Exit(1)

    console.print(f"[cyan]准备下载 {len(paper_ids)} 篇论文...[/cyan]")

    searcher = Searcher(config)
    downloader = PaperDownloader(config)

    success_count = 0
    failed_count = 0

    for paper_id in paper_ids:
        console.print(f"\n[dim]下载 {paper_id}...[/dim]")

        try:
            paper = searcher.get_paper_by_id(paper_id)

            if not paper:
                console.print(f"[red]未找到论文: {paper_id}[/red]")
                failed_count += 1
                continue

            pdf_url = searcher.get_pdf_url(paper)

            if not pdf_url:
                console.print(f"[yellow]无法找到 PDF 链接: {paper_id}[/yellow]")
                failed_count += 1
                continue

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                file_path = downloader.download_pdf(
                    paper=paper,
                    url=pdf_url,
                    progress=progress,
                )

            if index:
                downloader.index_paper(paper, file_path)

            success_count += 1
            console.print(f"[green]✓ {paper_id}[/green]")

        except Exception as e:
            console.print(f"[red]✗ {paper_id}: {e}[/red]")
            failed_count += 1

    console.print(f"\n[bold]下载完成[/bold]")
    console.print(f"  成功: [green]{success_count}[/green]")
    console.print(f"  失败: [red]{failed_count}[/red]")


@download_app.command("from-search")
def download_from_search(
    indices: Optional[str] = typer.Argument(None, help="论文编号，用逗号分隔 (如 1,2,3)"),
    all_papers: bool = typer.Option(False, "--all", "-a", help="下载搜索结果中的所有论文"),
) -> None:
    """
    从上次搜索结果下载论文。

    示例:
        acm download from-search 1,2,3
        acm download from-search --all
    """
    from acm_scholar_cli.search import _last_search_results

    if not _last_search_results:
        console.print("[bold yellow]请先执行搜索命令[/bold yellow]")
        raise typer.Exit(0)

    config = config_manager.load()

    if not config:
        console.print("[bold red]请先运行 'acm config init' 进行配置[/bold red]")
        raise typer.Exit(1)

    searcher = Searcher(config)
    downloader = PaperDownloader(config)

    if all_papers:
        papers_to_download = _last_search_results
        console.print(f"\n[cyan]准备下载所有 {len(papers_to_download)} 篇论文...[/cyan]")
    elif indices:
        indices_list = [int(i.strip()) for i in indices.split(",")]
        papers_to_download = [_last_search_results[i - 1] for i in indices_list if 0 < i <= len(_last_search_results)]
        console.print(f"\n[cyan]准备下载 {len(papers_to_download)} 篇论文...[/cyan]")
    else:
        # 交互式选择
        console.print("\n[bold cyan]选择要下载的论文[/bold cyan]")
        for idx, paper in enumerate(_last_search_results, 1):
            title = paper.get("title", "N/A")
            if len(title) > 60:
                title = title[:57] + "..."
            console.print(f"  {idx}. {title}")

        choice = Prompt.ask("\n输入论文编号 (多个用逗号分隔, 'q' 退出)", default="q")
        if choice.lower() == "q":
            raise typer.Exit(0)

        indices_list = [int(i.strip()) for i in choice.split(",")]
        papers_to_download = [_last_search_results[i - 1] for i in indices_list if 0 < i <= len(_last_search_results)]

    success_count = 0
    failed_count = 0

    for paper in papers_to_download:
        paper_id = paper.get("id", "").split("/")[-1]
        console.print(f"\n[dim]下载: {paper.get('title', 'N/A')[:50]}...[/dim]")

        try:
            pdf_url = searcher.get_pdf_url(paper)

            if not pdf_url:
                console.print(f"[yellow]无法找到 PDF 链接[/yellow]")
                failed_count += 1
                continue

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                file_path = downloader.download_pdf(
                    paper=paper,
                    url=pdf_url,
                    progress=progress,
                )

            downloader.index_paper(paper, file_path)
            success_count += 1
            console.print(f"[green]✓[/green]")

        except Exception as e:
            console.print(f"[red]✗ {e}[/red]")
            failed_count += 1

    console.print(f"\n[bold]下载完成[/bold]")
    console.print(f"  成功: [green]{success_count}[/green]")
    console.print(f"  失败: [red]{failed_count}[/red]")


@download_app.command("url")
def download_from_url(
    url: str = typer.Argument(..., help="PDF 直接下载链接"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="论文标题"),
) -> None:
    """
    通过 URL 直接下载 PDF。

    示例:
        acm download url "https://arxiv.org/pdf/2301.12345.pdf" --title "My Paper"
    """
    config = config_manager.load()

    if not config:
        console.print("[bold red]请先运行 'acm config init' 进行配置[/bold red]")
        raise typer.Exit(1)

    downloader = PaperDownloader(config)

    paper = {
        "title": title or "Unknown",
        "publication_year": 2024,
    }

    console.print(f"[cyan]正在下载 PDF...[/cyan]")

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            transient=True,
        ) as progress:
            file_path = downloader.download_pdf(
                paper=paper,
                url=url,
                progress=progress,
            )

        console.print(f"\n[bold green]✓ PDF 已下载到: {file_path}[/bold green]")

    except Exception as e:
        console.print(f"[bold red]下载失败: {e}[/bold red]")
        raise typer.Exit(1)
