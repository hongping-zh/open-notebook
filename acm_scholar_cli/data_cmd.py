"""数据统计命令 - 展示数据壁垒积累情况。"""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from acm_scholar_cli.data.storage import DataStorage

data_app = typer.Typer(
    name="data",
    help="查看数据积累统计（数据壁垒）",
    add_completion=False,
)

console = Console()


@data_app.command("stats")
def show_stats() -> None:
    """
    显示数据积累统计。

    示例:
        acm data stats
    """
    storage = DataStorage()
    stats = storage.get_all_stats()

    # 创建统计面板
    console.print("\n[bold cyan]📊 数据壁垒统计[/bold cyan]\n")

    # QA 语料库
    qa_stats = stats["qa_corpus"]
    qa_table = Table(title="问答语料库", show_header=False, box=None)
    qa_table.add_column("指标", style="dim")
    qa_table.add_column("数值", style="green")
    qa_table.add_row("总问答对数", str(qa_stats["total_qa_pairs"]))
    qa_table.add_row("有反馈的问答", str(qa_stats["pairs_with_feedback"]))
    qa_table.add_row("涉及论文数", str(qa_stats["unique_papers"]))
    console.print(qa_table)
    console.print()

    # 知识库
    kb_stats = stats["knowledge_base"]
    kb_table = Table(title="结构化知识库", show_header=False, box=None)
    kb_table.add_column("指标", style="dim")
    kb_table.add_column("数值", style="green")
    kb_table.add_row("已分析论文数", str(kb_stats["total_papers"]))
    kb_table.add_row("使用的模型", ", ".join(kb_stats["models_used"]) or "无")
    console.print(kb_table)
    console.print()

    # 图表分析
    fig_stats = stats["figures"]
    fig_table = Table(title="图表分析数据", show_header=False, box=None)
    fig_table.add_column("指标", style="dim")
    fig_table.add_column("数值", style="green")
    fig_table.add_row("已分析图表数", str(fig_stats["total_figures"]))
    fig_table.add_row("涉及论文数", str(fig_stats["unique_papers"]))
    console.print(fig_table)
    console.print()

    # 阅读会话
    rs_stats = stats["reading_sessions"]
    rs_table = Table(title="阅读行为数据", show_header=False, box=None)
    rs_table.add_column("指标", style="dim")
    rs_table.add_column("数值", style="green")
    rs_table.add_row("总阅读会话数", str(rs_stats["total_sessions"]))
    rs_table.add_row("总提问次数", str(rs_stats["total_questions"]))
    rs_table.add_row("总阅读时长(小时)", str(rs_stats["total_reading_time_hours"]))
    console.print(rs_table)

    # 总结
    total_data_points = (
        qa_stats["total_qa_pairs"] +
        kb_stats["total_papers"] +
        fig_stats["total_figures"] +
        rs_stats["total_sessions"]
    )

    console.print(Panel(
        f"[bold green]总数据点: {total_data_points}[/bold green]\n"
        f"[dim]每次使用都在积累有价值的数据，构建竞争壁垒[/dim]",
        title="数据飞轮",
        border_style="green",
    ))


@data_app.command("export")
def export_data(
    output_dir: str = typer.Option("./exports", "--output", "-o", help="导出目录"),
) -> None:
    """
    导出数据用于训练或分析。

    示例:
        acm data export --output ./my_exports
    """
    from pathlib import Path

    storage = DataStorage()
    output_path = Path(output_dir).expanduser()

    console.print(f"[cyan]导出数据到: {output_path}[/cyan]")

    exports = storage.export_for_training(output_path)

    console.print("\n[green]✓ 导出完成:[/green]")
    for name, path in exports.items():
        console.print(f"  - {name}: {path}")
