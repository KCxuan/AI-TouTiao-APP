# 这里会封装新闻模块增删改查的方法
from sqlalchemy.ext.asyncio import AsyncSession
from models.news import Category
from models.news import News
from sqlalchemy import select, func, Update, delete
from fastapi import HTTPException
from cache.news_cache import get_cached_categories, set_cached_categories, get_cache_news_list, set_cached_news_list, get_cached_news_detail, set_cached_news_detail,get_cached_related_news, set_cached_related_news, clear_news_list_cache, clear_related_news_by_category, clear_news_detail_cache, clear_all_related_news_cache
from fastapi.encoders import jsonable_encoder
from schemas.news import NewsCreateRequest, NewsUpdateRequest


# 获取新闻分类列表: 这里开始使用缓存
async def get_categories(
    db: AsyncSession,
    skip: int = 0, 
    limit: int = 100,
):
    # 尝试从缓存中获取新闻分类列表
    cached_categories = await get_cached_categories()
    if cached_categories is not None:
        return cached_categories


    # 如果缓存中没有数据，则写入缓存
    stmt = select(Category).offset(skip).limit(limit)
    result = await db.execute(stmt)
    categories = result.scalars().all()

    if categories is not None:
        json_categories = jsonable_encoder(categories) # 将ORM对象转换为JSON可序列化的形式
        await set_cached_categories(json_categories)

    # 返回数据
    return categories


# 获取新闻列表
async def get_news_list(db: AsyncSession, category_id: int, skip: int = 0, limit: int = 100):
    # 尝试从缓存中获取新闻列表
    cached_news_list = await get_cache_news_list(category_id, skip//limit + 1, limit)
    if cached_news_list is not None:
        # return cached_news_list 需要转化成ORM对象
        return [News(**item) for item in cached_news_list]
    
    # 查询指定分类下的所有新闻
    stmt = select(News).where(News.category_id == category_id).order_by(News.publish_time.desc(), News.id.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    news_list = result.scalars().all()

    # 如果缓存中没有数据，则写入缓存
    if news_list:
        json_news_list = jsonable_encoder(news_list) # 将ORM对象转换为JSON可序列化的形式
        await set_cached_news_list(category_id, skip//limit + 1, limit, json_news_list)


    return news_list

# 获取对应类别的新闻总数
async def get_news_count(db: AsyncSession, category_id: int):
    stmt = select(func.count(News.id)).where(News.category_id == category_id)
    result = await db.execute(stmt)
    return result.scalars().one() # 返回一个数字

# 获取新闻详情
# 响应结果： 当前新闻详情 + 增加一次浏览量 + 相关新闻 (同分类ID的新闻)
async def get_news_detail(db: AsyncSession, news_id: int):
    # 首先检查缓存里面有没有，有的化就直接返回
    cached_news_detail = await get_cached_news_detail(news_id=news_id)
    if cached_news_detail is not None:
        return News(**cached_news_detail) # 这里返回ORM对象

    # 现在缓存中并没有相关内容，那么就要查询数据库
    stmt = select(News).where(News.id == news_id)
    result = await db.execute(stmt)
    news_detail = result.scalars().one_or_none() 

    # 如果查到了，就要将其放到缓存中
    if news_detail:
        json_news_detail = jsonable_encoder(news_detail) # 将ORM对象转换为JSON可序列化的形式
        await set_cached_news_detail(news_id, json_news_detail)

    return news_detail



async def increase_news_views(db: AsyncSession, news_id: int):
    # 修改相关内容
    stmt = Update(News).where(News.id == news_id).values(views=News.views + 1)
    result = await db.execute(stmt)
    await db.flush() # 利用flush()方法同步数据库，但不会提交事务，由会话统一提交事务
    # 更新 -》检查数据库是否真的命中数据 -》 命中返回True
    return result.rowcount > 0

async def get_related_news(db: AsyncSession, news_id: int, category_id: int, limit: int = 5):
    # 尝试从缓存中获取相关新闻
    cached_related_news = await get_cached_related_news(news_id=news_id, category_id=category_id, limit=limit)
    if cached_related_news is not None:
        return [News(**item) for item in cached_related_news]

    # 如果缓存中没有，那么就到数据库查询相关新闻
    stmt = select(News).where(
        News.category_id == category_id,
        News.id != news_id
    ).order_by(
        News.views.desc(),
        News.publish_time.desc()
    ).limit(limit)

    result = await db.execute(stmt)
    related_news = result.scalars().all()

    # 如果查询到了相关新闻，就将其放到缓存中
    if related_news:
        json_related_news = jsonable_encoder(related_news) # 将ORM对象转换为JSON可序列化的形式
        await set_cached_related_news(news_id, category_id, limit, json_related_news)

    return related_news

# 发布新闻
async def create_news(db: AsyncSession, data: NewsCreateRequest, author: str, user_id: int):
    # 校验分类存在（否则 FK 报错会被兜底成"关联数据不存在"，信息不够友好）
    category = await db.get(Category, data.category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # 创建: views/publish_time/created_at/updated_at用模型默认就可以
    news_item = News(
        **data.model_dump(), 
        author=author,
        user_id=user_id,
        views=0,
    )
    db.add(news_item)
    await db.flush()
    await db.commit()

    # —— commit 之后才做缓存失效，时序正确 ——
    await clear_news_list_cache(data.category_id)
    await clear_related_news_by_category(data.category_id)

    return news_item

# 获取用户自己发布的新闻列表 要有total hasmore
async def get_user_news_list(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 10):
    stmt = select(News).where(News.user_id == user_id).order_by(News.publish_time.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

# 获取用户自己发布的新闻总数
async def get_user_news_count(db: AsyncSession, user_id: int):
    stmt = select(func.count(News.id)).where(News.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalars().one()

# 编辑新闻（先查再验权，只更新用户传入的字段）
async def update_news(db: AsyncSession, data: NewsUpdateRequest, user_id: int):
    # 文章必须存在
    news_item = await db.get(News, data.id)
    if news_item is None:
        raise HTTPException(status_code=404, detail="News not found")

    # 验身份 user_id = NULL 以及 别人的新闻不能编辑
    if news_item.user_id != user_id:
        raise HTTPException(status_code=403, detail="无权编辑该新闻")

    # 记录旧的分类ID
    old_category_id = news_item.category_id

    # 如果分类有变化 先检验新分类是否存在
    if data.category_id is not None and data.category_id != old_category_id:
        category = await db.get(Category, data.category_id)
        if category is None:
            raise HTTPException(status_code=404, detail="Category not found")

    # 部分更新
    updates = data.model_dump(exclude_unset=True)
    updates.pop("id", None) # id 是用来定位文章的，不是可以修改的字段
    for field, value in updates.items():
        setattr(news_item, field, value)

    await db.flush()
    await db.commit()

    # commit后清理缓存
    await clear_news_detail_cache(news_item.id) # 清除新闻详情缓存
    await clear_news_list_cache(old_category_id) # 清除旧分类的新闻列表缓存
    if data.category_id is not None and data.category_id != old_category_id:
        await clear_news_list_cache(data.category_id) # 清除新分类的新闻列表缓存
    
    await clear_all_related_news_cache() # 清除所有相关新闻缓存
    return news_item

# 删除新闻（先查再验权）
async def delete_news(db: AsyncSession, news_id: int, user_id: int):
    # 文章首先必须存在
    news_item = await db.get(News, news_id)
    if news_item is None:
        raise HTTPException(status_code=404, detail="News not found")

    # 看看是不是同一个作者
    if news_item.user_id != user_id:
        raise HTTPException(status_code=403, detail="无权删除该新闻")

    # 记录旧的分类ID，方便后续清除缓存
    old_category_id = news_item.category_id

    #  调用delete语句删除对应的新闻
    stmt = delete(News).where(News.id == news_id)
    await db.execute(stmt)

    await db.flush()
    await db.commit()

    # 接下来清除缓存， 删除新闻详情缓存，删除旧分类新闻列表缓存，删除所有相关新闻缓存
    await clear_news_detail_cache(news_item.id)
    await clear_news_list_cache(old_category_id)
    await clear_all_related_news_cache()

    return news_item





