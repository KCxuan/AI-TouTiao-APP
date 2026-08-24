# 存放新闻相关的缓存方法 新闻分类的读取和写入
from config.cache_conf import get_cache, set_cache, get_json_cache, delete_cache, delete_cache_pattern
from typing import List, Dict, Any, Optional

# key - value 缓存方法
CATEGORIES_KEY = "news:categories"
NEWS_LIST_PREFIX = "news_list:"
NEWS_DETAIL_PREFIX = "news_detail:"
RELATED_NEWS_PREFIX = "related_news:"



"""
下面存放新闻分类列表的缓存
"""
# 获取新闻分类缓存
async def get_cached_categories():
    return await get_json_cache(CATEGORIES_KEY)

# 写入新闻分类缓存 : 缓存的数据 过期的时间
async def set_cached_categories(data: List[Dict[str, Any]], expire: int = 7200):
    return await set_cache(CATEGORIES_KEY, data, expire)



"""
下面存放新闻列表的缓存
"""
# 写入缓存 - 新闻列表 key = news_list:分类id:页码:每页数量
async def set_cached_news_list(
    category_id: Optional[int], 
    page: int, 
    size: int, 
    news_list: List[Dict[str, Any]], 
    expire: int = 7200
):
    # 调用 封装的redis的设置方法，存放新闻列表到缓存
    category_id = "all" if category_id is None else category_id
    key = f"{NEWS_LIST_PREFIX}{category_id}:{page}:{size}"
    return await set_cache(key, news_list, expire)

# 读取缓存 - 新闻列表
async def get_cache_news_list(category_id: Optional[int], page: int, size: int):
    category_id = "all" if category_id is None else category_id
    key = f"{NEWS_LIST_PREFIX}{category_id}:{page}:{size}"
    return await get_json_cache(key)

# 删除缓存 - 新闻列表
async def clear_news_list_cache(category_id: Optional[int]):
    """发布/删除新闻后，清除该分类的所有列表缓存页"""
    return await delete_cache_pattern(f"{NEWS_LIST_PREFIX}{category_id}:*")


"""
下面存放新闻详情的缓存
"""
# 写入缓存 - 新闻详情 key = news_detail:新闻id
async def set_cached_news_detail(news_id: int, news_detail: Dict[str, Any], expire: int = 7200):
    key = f"{NEWS_DETAIL_PREFIX}{news_id}"
    return await set_cache(key, news_detail, expire)

# 读取缓存 - 新闻详情
async def get_cached_news_detail(news_id: int):
    key = f"{NEWS_DETAIL_PREFIX}{news_id}"
    return await get_json_cache(key)

# 精准清除某篇新闻的详情缓存（编辑/删除后调用，撕掉旧快照）
async def clear_news_detail_cache(news_id):
    return await delete_cache(f"{NEWS_DETAIL_PREFIX}{news_id}")

"""
下面存放相关新闻的缓存
"""
# 写入缓存 - 相关新闻 key = related_news:新闻id:分类id:限制显示数量
async def set_cached_related_news(news_id: int, category_id: int, limit: int, related_news: List[Dict[str, Any]], expire: int = 7200):
    key = f"{RELATED_NEWS_PREFIX}{news_id}:{category_id}:{limit}"
    return await set_cache(key, related_news, expire)


# 读取缓存 - 相关新闻
async def get_cached_related_news(news_id: int, category_id: int, limit: int):
    key = f"{RELATED_NEWS_PREFIX}{news_id}:{category_id}:{limit}"
    return await get_json_cache(key)

# 删除缓存 - 相关新闻
async def clear_related_news_by_category(category_id: int):
    key = f"{RELATED_NEWS_PREFIX}*:{category_id}:*"
    return await delete_cache_pattern(key)


# 全量清除相关新闻缓存（编辑/删除后调用，撤掉整面合影墙）
async def clear_all_related_news_cache():
    return await delete_cache_pattern(f"{RELATED_NEWS_PREFIX}*")