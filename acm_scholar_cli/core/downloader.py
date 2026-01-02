"""论文下载核心逻辑 - PDF 下载和索引建立。"""

from pathlib import Path
from typing import Optional
import httpx
from rich.progress import Progress
from acm_scholar_cli.config_manager import Config


class PaperDownloader:
    """论文下载器。"""

    def __init__(self, config: Config) -> None:
        """
        初始化下载器。

        Args:
            config: 配置对象
        """
        self.config = config
        self.download_dir = Path(config.download.directory or "~/acm-papers/").expanduser()
        self.download_dir.mkdir(parents=True, exist_ok=True)

    def download_pdf(
        self,
        paper: dict,
        url: str,
        progress: Optional[Progress] = None,
    ) -> Path:
        """
        下载论文 PDF。

        Args:
            paper: 论文信息字典
            url: PDF 下载 URL
            progress: Rich Progress 实例

        Returns:
            下载的文件路径
        """
        title = paper.get("title", "unknown")
        # 清理文件名中的非法字符
        safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "-", "_"))[:50]
        safe_title = safe_title.strip().replace(" ", "_")

        year = paper.get("publication_year", "unknown")
        authors = paper.get("authorships", [])
        if authors:
            first_author = authors[0].get("author", {}).get("display_name", "unknown")
            author_lastname = first_author.split()[-1] if " " in first_author else first_author
        else:
            author_lastname = "unknown"

        # 生成文件名
        filename = f"{author_lastname}_{year}_{safe_title}.pdf"
        file_path = self.download_dir / filename

        # 下载文件
        with httpx.stream("GET", url, follow_redirects=True, timeout=60.0) as response:
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))

            with open(file_path, "wb") as f:
                downloaded = 0
                for chunk in response.iter_bytes(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)

                    if progress and total_size > 0:
                        progress.update(
                            progress.tasks[0].id,
                            advance=len(chunk),
                            total=total_size,
                        )

        return file_path

    def index_paper(self, paper: dict, file_path: Path) -> str:
        """
        为论文建立索引。

        Args:
            paper: 论文信息字典
            file_path: PDF 文件路径

        Returns:
            索引 ID
        """
        # 检查是否配置了 SurrealDB
        if not self.config.database.host:
            console.print("[yellow]未配置数据库，跳过索引建立[/yellow]")
            return ""

        # 提取 PDF 文本
        text = self._extract_text(file_path)

        # 分块处理
        chunks = self._chunk_text(text)

        # 生成向量
        embeddings = self._generate_embeddings(chunks)

        # 存储到数据库
        paper_id = self._store_in_db(paper, chunks, embeddings)

        return paper_id

    def _extract_text(self, file_path: Path) -> str:
        """
        从 PDF 中提取文本。

        Args:
            file_path: PDF 文件路径

        Returns:
            提取的文本
        """
        try:
            import pypdf

            reader = pypdf.PdfReader(str(file_path))
            text_parts = []

            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)

            return "\n\n".join(text_parts)
        except Exception as e:
            raise Exception(f"PDF 文本提取失败: {e}")

    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> list:
        """
        将文本分块。

        Args:
            text: 原始文本
            chunk_size: 块大小
            overlap: 重叠大小

        Returns:
            文本块列表
        """
        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = min(start + chunk_size, text_len)
            chunks.append(text[start:end])
            start = end - overlap

            if start >= text_len:
                break

        return chunks

    def _generate_embeddings(self, chunks: list) -> list:
        """
        为文本块生成向量嵌入。

        Args:
            chunks: 文本块列表

        Returns:
            向量列表
        """
        # 检查是否配置了 LLM API
        if self.config.llm.api_key and self.config.llm.provider != "ollama":
            return self._generate_remote_embeddings(chunks)
        else:
            return self._generate_local_embeddings(chunks)

    def _generate_remote_embeddings(self, chunks: list) -> list:
        """
        使用远程 API 生成嵌入。

        Args:
            chunks: 文本块列表

        Returns:
            向量列表
        """
        # 这里可以集成 OpenAI 或其他嵌入 API
        # 目前返回空列表占位
        console.print("[yellow]使用远程嵌入 API[/yellow]")
        return []

    def _generate_local_embeddings(self, chunks: list) -> list:
        """
        使用本地模型生成嵌入。

        Args:
            chunks: 文本块列表

        Returns:
            向量列表
        """
        try:
            from sentence_transformers import SentenceTransformer

            console.print("[cyan]使用本地嵌入模型...[/cyan]")
            model = SentenceTransformer("all-MiniLM-L6-v2")
            embeddings = model.encode(chunks, show_progress_bar=True)
            return embeddings.tolist()
        except ImportError:
            console.print("[yellow]sentence-transformers 未安装，跳过嵌入生成[/yellow]")
            return []

    def _store_in_db(
        self,
        paper: dict,
        chunks: list,
        embeddings: list,
    ) -> str:
        """
        存储到 SurrealDB。

        Args:
            paper: 论文信息
            chunks: 文本块
            embeddings: 向量

        Returns:
            存储的 ID
        """
        # 这里可以集成 SurrealDB 客户端
        console.print("[cyan]存储到数据库...[/cyan]")
        return ""
