"""
论文检索模块 - 使用arXiv API获取最新论文
"""
import arxiv
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class Paper:
    """论文数据模型"""
    def __init__(
        self,
        title: str,
        authors: List[str],
        abstract: str,
        url: str,
        published: datetime,
        categories: List[str]
    ):
        self.title = title
        self.authors = authors
        self.abstract = abstract
        self.url = url
        self.published = published
        self.categories = categories

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "title": self.title,
            "authors": self.authors,
            "abstract": self.abstract,
            "url": self.url,
            "published": self.published.isoformat(),
            "categories": self.categories
        }


class PaperFetcher:
    """论文检索器"""

    def __init__(self, max_papers: int = 5, days_back: int = 1):
        self.max_papers = max_papers
        self.days_back = days_back
        self.client = arxiv.Client()

    def _build_query(self, keywords: List[str]) -> str:
        """构建搜索查询"""
        keyword_queries = []
        for keyword in keywords:
            # 处理带空格的关键词
            if " " in keyword:
                keyword_queries.append(f'ti:"{keyword}" OR abs:"{keyword}"')
            else:
                keyword_queries.append(f'ti:{keyword} OR abs:{keyword}')

        # 组合所有关键词，用OR连接
        query = " OR ".join(keyword_queries)
        return query

    def _is_recent_enough(self, published_date: datetime) -> bool:
        """检查论文是否足够新"""
        cutoff_date = datetime.now(published_date.tzinfo) - timedelta(days=self.days_back)
        return published_date >= cutoff_date

    def fetch_papers(self, keywords: List[str]) -> List[Paper]:
        """
        根据关键词搜索最新论文

        Args:
            keywords: 关键词列表

        Returns:
            论文列表
        """
        logger.info(f"开始搜索论文，关键词: {keywords}")

        query = self._build_query(keywords)

        # 构建搜索
        search = arxiv.Search(
            query=query,
            max_results=self.max_papers * 3,  # 获取更多结果用于过滤
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending
        )

        papers = []
        try:
            for result in self.client.results(search):
                if len(papers) >= self.max_papers:
                    break

                if self._is_recent_enough(result.published):
                    paper = Paper(
                        title=result.title,
                        authors=[author.name for author in result.authors],
                        abstract=result.summary,
                        url=result.entry_id,
                        published=result.published,
                        categories=result.categories
                    )
                    papers.append(paper)
                    logger.info(f"找到论文: {paper.title}")

        except Exception as e:
            logger.error(f"搜索论文时出错: {e}")

        logger.info(f"共找到 {len(papers)} 篇论文")
        return papers

    def fetch_papers_by_category(
        self,
        categories: List[str],
        keywords: Optional[List[str]] = None
    ) -> List[Paper]:
        """
        根据分类和关键词搜索论文

        Args:
            categories: arXiv分类列表，如 ['cs.AI', 'cs.LG']
            keywords: 可选关键词列表

        Returns:
            论文列表
        """
        category_query = " OR ".join([f"cat:{cat}" for cat in categories])

        if keywords:
            keyword_query = self._build_query(keywords)
            query = f"({category_query}) AND ({keyword_query})"
        else:
            query = category_query

        search = arxiv.Search(
            query=query,
            max_results=self.max_papers * 3,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending
        )

        papers = []
        try:
            for result in self.client.results(search):
                if len(papers) >= self.max_papers:
                    break

                if self._is_recent_enough(result.published):
                    paper = Paper(
                        title=result.title,
                        authors=[author.name for author in result.authors],
                        abstract=result.summary,
                        url=result.entry_id,
                        published=result.published,
                        categories=result.categories
                    )
                    papers.append(paper)

        except Exception as e:
            logger.error(f"搜索论文时出错: {e}")

        return papers
