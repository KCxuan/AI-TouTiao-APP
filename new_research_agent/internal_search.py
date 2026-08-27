import asyncio

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from config.db_config import DATABASE_URL
from crud.news import search_news_by_keyword
from models.news import News
from new_research_agent.search_types import SearchResult
"""
研究图跑在 to_thread 里，和 FastAPI 的事件循环不是同一个，
所以不要直接拿 get_database() 那个会话。
下面用「每次搜索临时建引擎」的方式避开这个问题。
"""

def _news_to_search_result(news: News) -> SearchResult:
    """把站内新闻转成和 Tavily 相同的来源结构。"""
    snippet = (news.description or "").strip()
    if not snippet and news.content:
        snippet = news.content.strip()[:180]

    published_at = None
    if news.publish_time is not None:
        published_at = news.publish_time.isoformat(sep=" ", timespec="minutes")

    return {
        "title": news.title,
        # 用独立 URL 方案，避免和站外 https 链接撞车。
        "url": f"internal://news/{news.id}",
        "snippet": snippet or "暂无简介",
        "publisher": news.author or "站内新闻",
        "published_at": published_at,
        "source_type": "internal",
    }


_STOP_WORDS = {
    "的",
    "了",
    "与",
    "及",
    "和",
    "在",
    "是",
    "对",
    "等",
    "相关",
    "新闻",
    "研究",
    "最近",
    "近期",
    "目前",
    "发展",
    "历程",
    "情况",
    "问题",
    "分析",
    "报道",
    "进展",
    "影响",
}


def _normalize_keywords(keywords: list[str]) -> list[str]:
    """去掉空词、停用词和重复项，最多保留 5 个实体短词。"""
    normalized: list[str] = []
    for raw in keywords:
        item = raw.strip()
        if len(item) < 2 or item in _STOP_WORDS:
            continue
        if item in normalized:
            continue
        normalized.append(item)
        if len(normalized) >= 5:
            break
    return normalized


async def _search_internal_news_async(
    keywords: list[str],
    max_results: int,
) -> list[SearchResult]:
    keywords = _normalize_keywords(keywords)
    if not keywords or max_results <= 0:
        return []

    engine = create_async_engine(DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(
        engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )
    seen_ids: set[int] = set()
    results: list[SearchResult] = []
    try:
        async with session_factory() as session:
            for keyword in keywords:
                if len(results) >= max_results:
                    break
                news_list = await search_news_by_keyword(
                    db=session,
                    keyword=keyword,
                    category_id=None,
                    skip=0,
                    limit=max_results,
                )
                for news in news_list:
                    if news.id in seen_ids:
                        continue
                    seen_ids.add(news.id)
                    results.append(_news_to_search_result(news))
                    if len(results) >= max_results:
                        break
    finally:
        await engine.dispose()

    return results


def search_internal_news(
    keywords: list[str],
    max_results: int = 5,
) -> list[SearchResult]:
    """
    给同步的 LangGraph 节点调用。
    每个关键词走首页同一套 search_news_by_keyword，按新闻 id 去重。
    """
    return asyncio.run(
        _search_internal_news_async(keywords, max_results)
    )