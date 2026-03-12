"""
业界资讯检索模块
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
import re
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)


class NewsArticle:
    """资讯文章数据模型"""
    def __init__(
        self,
        title: str,
        summary: str,
        url: str,
        source: str,
        published: Optional[datetime] = None
    ):
        self.title = title
        self.summary = summary
        self.url = url
        self.source = source
        self.published = published or datetime.now()

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "title": self.title,
            "summary": self.summary,
            "url": self.url,
            "source": self.source,
            "published": self.published.isoformat()
        }


class NewsFetcher:
    """业界资讯检索器"""

    def __init__(self, max_news: int = 5, days_back: int = 1):
        self.max_news = max_news
        self.days_back = days_back
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

    def _search_hn(self, keyword: str) -> List[NewsArticle]:
        """搜索Hacker News"""
        articles = []
        try:
            query = quote_plus(keyword)
            url = f"https://hn.algolia.com/api/v1/search?query={query}&tags=story&numericFilters=created_at_i>{int((datetime.now() - timedelta(days=self.days_back)).timestamp())}"

            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            for hit in data.get("hits", [])[:self.max_news]:
                article = NewsArticle(
                    title=hit.get("title", ""),
                    summary=f"Points: {hit.get('points', 0)}, Comments: {hit.get('num_comments', 0)}",
                    url=hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                    source="Hacker News",
                    published=datetime.fromtimestamp(hit.get("created_at_i", 0))
                )
                articles.append(article)

        except Exception as e:
            logger.warning(f"搜索Hacker News失败: {e}")

        return articles

    def _search_reddit(self, keyword: str, subreddits: List[str] = None) -> List[NewsArticle]:
        """搜索Reddit"""
        if subreddits is None:
            subreddits = ["MachineLearning", "artificial", "LLM", "LocalLLaMA"]

        articles = []
        try:
            query = quote_plus(keyword)
            for subreddit in subreddits[:2]:
                url = f"https://www.reddit.com/r/{subreddit}/search.json?q={query}&restrict_sr=1&sort=new&t=week"
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()

                for post in data.get("data", {}).get("children", [])[:3]:
                    post_data = post.get("data", {})
                    created_utc = post_data.get("created_utc")
                    if created_utc:
                        published = datetime.fromtimestamp(created_utc)
                        if (datetime.now() - published).days > self.days_back:
                            continue

                    article = NewsArticle(
                        title=post_data.get("title", ""),
                        summary=f"Score: {post_data.get('score', 0)}",
                        url=f"https://reddit.com{post_data.get('permalink', '')}",
                        source=f"Reddit r/{subreddit}",
                        published=datetime.fromtimestamp(post_data.get("created_utc", 0)) if post_data.get("created_utc") else None
                    )
                    articles.append(article)

        except Exception as e:
            logger.warning(f"搜索Reddit失败: {e}")

        return articles

    def _search_github_trending(self, keyword: str) -> List[NewsArticle]:
        """搜索GitHub趋势项目"""
        articles = []
        try:
            url = f"https://github.com/trending?since=daily"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            repos = soup.find_all("article", class_="Box-row")

            for repo in repos[:self.max_news]:
                try:
                    name_elem = repo.find("h2", class_="h3")
                    if not name_elem:
                        continue

                    repo_name = name_elem.get_text(strip=True).replace(" ", "")
                    desc_elem = repo.find("p", class_="col-9")
                    description = desc_elem.get_text(strip=True) if desc_elem else ""

                    # 简单关键词匹配
                    if keyword.lower() in (repo_name + " " + description).lower():
                        article = NewsArticle(
                            title=repo_name,
                            summary=description,
                            url=f"https://github.com/{repo_name}",
                            source="GitHub Trending"
                        )
                        articles.append(article)
                except Exception:
                    continue

        except Exception as e:
            logger.warning(f"搜索GitHub失败: {e}")

        return articles

    def fetch_news(self, keywords: List[str]) -> List[NewsArticle]:
        """
        根据关键词搜索业界资讯

        Args:
            keywords: 关键词列表

        Returns:
            资讯列表
        """
        logger.info(f"开始搜索业界资讯，关键词: {keywords}")

        all_articles = []
        seen_urls = set()

        for keyword in keywords[:3]:
            # 从多个来源搜索
            hn_articles = self._search_hn(keyword)
            reddit_articles = self._search_reddit(keyword)
            github_articles = self._search_github_trending(keyword)

            for article in hn_articles + reddit_articles + github_articles:
                if article.url not in seen_urls:
                    seen_urls.add(article.url)
                    all_articles.append(article)

        # 按时间排序（最新的在前）
        all_articles.sort(key=lambda x: x.published, reverse=True)

        result = all_articles[:self.max_news]
        logger.info(f"共找到 {len(result)} 条资讯")
        return result
