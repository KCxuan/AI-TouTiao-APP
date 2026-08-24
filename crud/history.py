from models.news import News
from models.history import History
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,func, delete, update


# 添加浏览历史
async def add_history(
    user_id: int, 
    news_id: int, 
    db: AsyncSession
):
    """
    这里的添加浏览历史要分两种情况讨论：
    1. 用户之前没有浏览过该新闻，则添加新的浏览历史记录。
    2. 用户之前已经浏览过该新闻，则更新浏览历史记录的浏览时间。
    """
    watch_already_query = select(History).where(History.user_id == user_id, History.news_id == news_id)
    result = await db.execute(watch_already_query)
    existing_history = result.scalars().first()
    if existing_history:
        # 这里说明已经浏览过了，更新浏览时间
        update_query = update(History).where(History.user_id == user_id, History.news_id == news_id).values(view_time=func.now())
        await db.execute(update_query)
        await db.flush()
        await db.refresh(existing_history)
        return existing_history
    else:
        # 这里说明还没有浏览过，添加新的浏览历史记录
        db_history = History(user_id=user_id, news_id=news_id)
        db.add(db_history)
        await db.flush()
        await db.refresh(db_history)
        return db_history

# 获取浏览历史列表
async def get_history_list(
    page: int,
    page_size: int,
    user_id: int,
    db: AsyncSession
):
    # 获取浏览的历史纪录的总量 + 历史记录列表
    count_query = select(func.count()).where(History.user_id == user_id)
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    # 获取收藏的新闻列表，这里要联表查询join + 分页 + 顺手排个序（收藏时间）
    # 联表查询，select中放置查询主题模型类以及字段别名（可选），join中放联合查询的模型类 以及 联合查询的条件
    query = select(
        News,
        History.view_time.label("view_time"),
        History.id.label("history_id"),
    ).join(
        History,
        History.news_id == News.id
    ).where(
        History.user_id == user_id
    ).order_by(
        History.view_time.desc()
    ).offset((page - 1) * page_size).limit(page_size)
    """
    [
        (新闻对象，历史纪录的id)
    ]
    """
    result = await db.execute(query)
    return result.all(), total


# 删除单条历史记录
async def remove_history_record(
    history_id: int,
    user_id: int,
    db: AsyncSession
):
    delete_query = delete(History).where(History.user_id == user_id, History.id == history_id)
    result = await db.execute(delete_query)
    return result.rowcount > 0

# 清空历史浏览列表
async def clear_history_list(
    user_id: int,
    db: AsyncSession
):
    delete_query = delete(History).where(History.user_id == user_id)
    result = await db.execute(delete_query)
    return result.rowcount or 0

