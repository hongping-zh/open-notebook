"""数据库模块 - SurrealDB 连接和操作。"""

from typing import Optional, list, Any
from acm_scholar_cli.config_manager import Config


class SurrealDBClient:
    """SurrealDB 客户端。"""

    def __init__(self, config: Config) -> None:
        """
        初始化 SurrealDB 客户端。

        Args:
            config: 配置对象
        """
        self.config = config
        self.host = config.database.host
        self.port = config.database.port
        self.user = config.database.user
        self.password = config.database.password
        self.client = None

    def connect(self) -> bool:
        """
        连接到 SurrealDB。

        Returns:
            是否连接成功
        """
        if not self.host:
            return False

        try:
            import surrealdb

            self.client = surrealdb.Server(
                f"ws://{self.host}:{self.port}",
                user=self.user,
                password=self.password,
            )
            return True
        except Exception:
            return False

    def create_tables(self) -> None:
        """
        创建必要的表和索引。
        """
        if not self.client:
            return

        try:
            # 创建论文表
            self.client.query("CREATE TABLE IF NOT EXISTS papers")

            # 创建文本块表
            self.client.query("CREATE TABLE IF NOT EXISTS chunks")

            # 创建索引
            self.client.query("DEFINE INDEX paper_id ON papers FIELDS id")
            self.client.query("DEFINE INDEX chunk_embedding ON chunks FIELDS embedding")
        except Exception as e:
            raise Exception(f"创建表失败: {e}")

    def add_paper(self, paper: dict) -> str:
        """
        添加论文到数据库。

        Args:
            paper: 论文信息字典

        Returns:
            创建的记录 ID
        """
        if not self.client:
            return ""

        try:
            result = self.client.query(
                "CREATE papers SET "
                f"id = '{paper.get('id', '')}', "
                f"title = '{paper.get('title', '').replace(chr(39), chr(39) + chr(39))}', "
                f"authors = {paper.get('authorships', [])}, "
                f"year = {paper.get('publication_year', 0)}, "
                f"abstract = '{paper.get('abstract', '').replace(chr(39), chr(39) + chr(39))}', "
                f"local_path = '{paper.get('local_path', '')}', "
                f"doi = '{paper.get('doi', '')}', "
                f"created_at = time::now()"
            )
            return str(result)
        except Exception as e:
            raise Exception(f"添加论文失败: {e}")

    def add_chunk(self, paper_id: str, content: str, embedding: list) -> str:
        """
        添加文本块到数据库。

        Args:
            paper_id: 论文 ID
            content: 文本内容
            embedding: 向量嵌入

        Returns:
            创建的记录 ID
        """
        if not self.client:
            return ""

        try:
            result = self.client.query(
                "CREATE chunks SET "
                f"paper_id = '{paper_id}', "
                f"content = '{content.replace(chr(39), chr(39) + chr(39))}', "
                f"embedding = {embedding}"
            )
            return str(result)
        except Exception as e:
            raise Exception(f"添加文本块失败: {e}")

    def search_papers(self, query: str, limit: int = 10) -> list:
        """
        搜索论文。

        Args:
            query: 搜索查询
            limit: 结果数量限制

        Returns:
            论文列表
        """
        if not self.client:
            return []

        try:
            result = self.client.query(
                f"SELECT * FROM papers WHERE title CONTAINS '{query}' LIMIT {limit}"
            )
            return result or []
        except Exception as e:
            raise Exception(f"搜索论文失败: {e}")

    def semantic_search(
        self,
        query_embedding: list,
        limit: int = 5,
    ) -> list:
        """
        向量相似性搜索。

        Args:
            query_embedding: 查询向量
            limit: 结果数量限制

        Returns:
            匹配的文本块列表
        """
        if not self.client:
            return []

        try:
            # SurrealDB 的向量搜索语法
            result = self.client.query(
                f"SELECT *, vector::similarity::cosine(embedding, {query_embedding}) as score "
                f"FROM chunks ORDER BY score DESC LIMIT {limit}"
            )
            return result or []
        except Exception as e:
            raise Exception(f"向量搜索失败: {e}")

    def get_paper(self, paper_id: str) -> Optional[dict]:
        """
        获取论文详情。

        Args:
            paper_id: 论文 ID

        Returns:
            论文信息字典
        """
        if not self.client:
            return None

        try:
            result = self.client.query(f"SELECT * FROM papers WHERE id = '{paper_id}'")
            return result[0] if result else None
        except Exception as e:
            raise Exception(f"获取论文失败: {e}")

    def delete_paper(self, paper_id: str) -> bool:
        """
        删除论文及其关联的文本块。

        Args:
            paper_id: 论文 ID

        Returns:
            是否成功删除
        """
        if not self.client:
            return False

        try:
            # 删除论文
            self.client.query(f"DELETE FROM papers WHERE id = '{paper_id}'")
            # 删除关联的文本块
            self.client.query(f"DELETE FROM chunks WHERE paper_id = '{paper_id}'")
            return True
        except Exception as e:
            raise Exception(f"删除论文失败: {e}")

    def get_stats(self) -> dict:
        """
        获取数据库统计信息。

        Returns:
            统计信息字典
        """
        if not self.client:
            return {}

        try:
            paper_count = self.client.query("SELECT count() FROM papers")[0].get("count", 0)
            chunk_count = self.client.query("SELECT count() FROM chunks")[0].get("count", 0)

            return {
                "paper_count": paper_count,
                "chunk_count": chunk_count,
            }
        except Exception as e:
            raise Exception(f"获取统计信息失败: {e}")

    def close(self) -> None:
        """关闭数据库连接。"""
        if self.client:
            self.client.close()
