from typing_extensions import TypedDict


class SearchResult(TypedDict):
    """搜索工具返回的一条标准化新闻结果。"""

    title: str
    url: str
    snippet: str
    publisher: str | None
    published_at: str | None