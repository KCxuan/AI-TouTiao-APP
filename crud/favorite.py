from models.news import News
from models.favorite import Favorite
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,func, delete


# 判断新闻是否被收藏
async def is_news_favorite(
    user_id: int,
    news_id: int,
    db: AsyncSession
):
    query = select(Favorite).where(Favorite.user_id == user_id, Favorite.news_id == news_id)
    result = await db.execute(query)
    # 判断是否收藏了该新闻
    return result.scalar_one_or_none() is not None

# 添加收藏
async def add_favorite(
    user_id: int,
    news_id: int,
    db: AsyncSession
):
    db_favorite = Favorite(user_id=user_id, news_id=news_id)
    db.add(db_favorite)
    await db.flush()
    await db.refresh(db_favorite)
    return db_favorite

# 删除收藏
async def remove_news_favorite(
    user_id: int,
    news_id: int,
    db: AsyncSession
):

    stmt = delete(Favorite).where(Favorite.user_id == user_id, Favorite.news_id == news_id)
    result = await db.execute(stmt)
    return result.rowcount > 0


# 获取收藏的新闻列表:获取的是某个用户的收藏列表 + 分页功能
async def get_favorite_list(
    user_id: int,
    page: int,
    page_size: int,
    db: AsyncSession
):
    # 获取收藏的新闻总量 + 收藏的新闻列表
    count_query = select(func.count()).where(Favorite.user_id == user_id)
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    # 获取收藏的新闻列表，这里要联表查询join + 分页 + 顺手排个序（收藏时间）
    # 联表查询，select中放置查询主题模型类以及字段别名（可选），join中放联合查询的模型类 以及 联合查询的条件
    query = select(
        News, 
        Favorite.created_at.label("favorite_time"), 
        Favorite.id.label("favorite_id")
    ).join(
        Favorite, News.id == Favorite.news_id
    ).where(
        Favorite.user_id == user_id
    ).order_by(
        Favorite.created_at.desc()
    ).offset((page - 1) * page_size).limit(page_size)
    """
    [
        (新闻对象, 收藏时间, 收藏id)
    ]
    """
    result = await db.execute(query)
    return result.all(), total

# 清空当前用户的收藏列表
async def clear_favorite(
    user_id: int,
    db: AsyncSession
):
    delete_query = delete(Favorite).where(Favorite.user_id == user_id)
    result = await db.execute(delete_query)
    return result.rowcount or 0
