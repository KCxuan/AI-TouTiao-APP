from new_research_agent.search_types import (
    SearchResult,
)
from ddgs import DDGS
from urllib.parse import urlparse

from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

class FakeNewsSearchTool:
    """返回固定数据的新闻搜索工具。"""

    def search(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[SearchResult]:
        """
        根据搜索词返回模拟新闻。

        当前只用于验证搜索工具与节点之间的边界。
        """

        results: list[SearchResult]

        # 证据审查产生的第二轮搜索词会包含这个短语。
        if "不同媒体观点" in query:
            results = [
                {
                    "title": "示例新闻：市场反应",
                    "url": (
                        "https://example.org/news/"
                        "market-response"
                    ),
                    "snippet": (
                        f"不同媒体分析了“{query}”"
                        "相关事件的市场反应。"
                    ),
                    "publisher": "示例科技媒体 B",
                    "published_at": "2026-08-21",
                },
                {
                    "title": "示例新闻：行业观点",
                    "url": (
                        "https://example.net/news/"
                        "industry-opinion"
                    ),
                    "snippet": (
                        f"行业人士分析了“{query}”"
                        "可能产生的影响。"
                    ),
                    "publisher": "示例行业媒体 C",
                    "published_at": "2026-08-22",
                },
            ]

        # 用户直接回车要求补查时，查询词会包含“更多”。
        elif "更多" in query or "补充" in query:
            results = [
                {
                    "title": "示例新闻：补充报道",
                    "url": (
                        "https://example.com/news/"
                        "additional-report"
                    ),
                    "snippet": (
                        f"这是围绕“{query}”"
                        "获得的补充资料。"
                    ),
                    "publisher": "示例补充媒体 D",
                    "published_at": "2026-08-23",
                }
            ]

        # 第一次搜索返回一条来源，让证据审查触发第二轮。
        else:
            results = [
                {
                    "title": "示例新闻：相关产品发布",
                    "url": (
                        "https://example.com/news/"
                        "product-release"
                    ),
                    "snippet": (
                        f"围绕“{query}”发现了一条"
                        "相关产品发布报道。"
                    ),
                    "publisher": "示例科技媒体 A",
                    "published_at": "2026-08-20",
                }
            ]

        return results[:max_results]


class DDGSNewsSearchTool:
    """使用 DDGS 搜索最近一周的真实新闻。"""

    def search(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[SearchResult]:
        raw_results = DDGS().news(
            query=query,

            # 当前项目主要使用中文查询。
            # 搜索范围设为全球，中文查询仍会优先返回中文内容。
            region="wt-wt",

            # 当前新闻研究默认关注最近一周。
            timelimit="w",

            max_results=max_results,
        )

        return [
            {
                "title": item["title"],
                "url": item["url"],

                # DDGS 使用 body 保存新闻摘要。
                "snippet": item["body"],

                # DDGS 使用 source 保存媒体名称。
                "publisher": (
                    item["source"] or None
                ),

                # DDGS 使用 date 保存发布时间。
                "published_at": (
                    item["date"] or None
                ),
            }
            for item in raw_results
        ]


class TavilyNewsSearchTool:
    """使用 Tavily 搜索真实新闻。"""

    def __init__(self) -> None:
        self.client = TavilyClient()

    def search(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[SearchResult]:
        response = self.client.search(
            query=query,

            # 使用 Tavily 的新闻搜索模式。
            topic="news",

            # basic 每次只消耗 1 credit。
            search_depth="basic",

            # 当前新闻研究默认关注最近一周。
            time_range="week",

            max_results=max_results,
        )

        return [
            {
                "title": item["title"],
                "url": item["url"],

                # Tavily 使用 content 保存搜索摘要。
                "snippet": item["content"],

                # Tavily 没有统一媒体字段，
                # 第一版使用 URL 域名作为来源。
                "publisher": (
                    urlparse(item["url"])
                    .netloc
                    .removeprefix("www.")
                    or None
                ),

                # 新闻结果可能包含发布时间。
                "published_at": item.get(
                    "published_date"
                ),
            }
            for item in response["results"]
        ]


news_search_tool = TavilyNewsSearchTool()