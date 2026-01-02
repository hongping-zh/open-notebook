"""论文搜索核心逻辑 - 通过 OpenAlex API 实现搜索功能。"""

from typing import Optional
from urllib.parse import quote
import httpx
import asyncio
from acm_scholar_cli.config_manager import Config


class Searcher:
    """论文搜索器 - 使用 OpenAlex API。"""

    BASE_URL = "https://api.openalex.org"

    def __init__(self, config: Config) -> None:
        """
        初始化搜索器。

        Args:
            config: 配置对象
        """
        self.config = config
        self.email = config.openalex.email

    def _get_headers(self) -> dict:
        """
        获取请求头，包含 OpenAlex 需要的邮箱信息。

        Returns:
            请求头字典
        """
        headers = {
            "Accept": "application/json",
        }
        if self.email:
            headers["User-Agent"] = f"ACM Scholar CLI (mailto:{self.email})"
        return headers

    async def search_async(
        self,
        query: str,
        year: Optional[int] = None,
        limit: int = 10,
        min_citations: Optional[int] = None,
    ) -> list:
        """
        异步搜索论文。
        """
        filters = [
            "type:article",
        ]

        if year:
            filters.append(f"publication_year:{year}")

        if min_citations is not None:
            filters.append(f"cited_by_count:>={min_citations}")

        filter_str = ",".join(filters)
        encoded_query = quote(query)

        url = f"{self.BASE_URL}/works?search={encoded_query}&filter={filter_str}&per-page={limit}"

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url, headers=self._get_headers())
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])

    def search(
        self,
        query: str,
        year: Optional[int] = None,
        limit: int = 10,
        min_citations: Optional[int] = None,
    ) -> list:
        """
        搜索论文（同步方法）。

        Args:
            query: 搜索关键词
            year: 筛选特定年份
            limit: 结果数量限制
            min_citations: 最低引用数

        Returns:
            论文列表
        """
        try:
            return asyncio.run(
                self.search_async(query, year, limit, min_citations)
            )
        except Exception as e:
            raise Exception(f"搜索失败: {e}")

    async def search_acm_async(
        self,
        query: str,
        year: Optional[int] = None,
        limit: int = 10,
    ) -> list:
        """
        异步搜索 ACM 论文。
        """
        filters = [
            "type:article",
        ]

        if year:
            filters.append(f"publication_year:{year}")

        filter_str = ",".join(filters)
        encoded_query = quote(query)

        url = f"{self.BASE_URL}/works?search={encoded_query}&filter={filter_str}&per-page={limit}"

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url, headers=self._get_headers())
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])

            # 过滤 ACM 相关的论文
            acm_papers = []
            for paper in results:
                host_organizations = paper.get("host_organizations", [])
                for org in host_organizations:
                    if "acm" in org.get("display_name", "").lower():
                        acm_papers.append(paper)
                        break

                pub_title = paper.get("publication_title", "").lower()
                if "acm" in pub_title:
                    if paper not in acm_papers:
                        acm_papers.append(paper)

            return acm_papers

    def search_acm(
        self,
        query: str,
        year: Optional[int] = None,
        limit: int = 10,
    ) -> list:
        """
        专门搜索 ACM 出版物中的论文（同步方法）。
        """
        try:
            return asyncio.run(self.search_acm_async(query, year, limit))
        except Exception as e:
            raise Exception(f"搜索失败: {e}")

    async def get_paper_by_id_async(self, paper_id: str) -> Optional[dict]:
        """
        异步获取论文详情。
        """
        url = f"{self.BASE_URL}/works/{paper_id}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=self._get_headers())
            if response.status_code == 200:
                return response.json()
            return None

    def get_paper_by_id(self, paper_id: str) -> Optional[dict]:
        """
        通过 ID 获取论文详情（同步方法）。
        """
        try:
            return asyncio.run(self.get_paper_by_id_async(paper_id))
        except Exception:
            return None

    async def get_pdf_url_async(self, paper: dict) -> Optional[str]:
        """
        异步获取论文的 PDF 下载 URL。
        """
        open_access = paper.get("open_access", {})
        if open_access.get("is_oa", False):
            oa_url = open_access.get("oa_url")
            if oa_url:
                return oa_url

        locations = paper.get("locations", [])
        for location in locations:
            source = location.get("source", {})
            if source.get("host_organization") == "arXiv":
                return location.get("landing_page_url")

        for location in locations:
            source = location.get("source", {})
            if "pubmed" in source.get("display_name", "").lower():
                return location.get("landing_page_url")

        for location in locations:
            if location.get("is_oa"):
                return location.get("landing_page_url")

        return None

    def get_pdf_url(self, paper: dict) -> Optional[str]:
        """
        获取论文的 PDF 下载 URL（同步方法）。
        """
        try:
            return asyncio.run(self.get_pdf_url_async(paper))
        except Exception:
            return None
