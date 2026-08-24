from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import delete
from config import db_config
from sqlalchemy.ext.asyncio import AsyncSession
from crud import news
from schemas.news import NewsCreateRequest, NewsUpdateRequest
from models.users import User
from utils.auth import get_current_user
from utils.response import success_response

# 创建一个 APIRouter 实例
router = APIRouter(prefix="/api/news", tags=["news"])

# 接口实现流程
# 1.模块化路由 -> API 接口规范文档
# 2.定义模型类 -> 数据库表（数据库设计文档）
# 3.在CRUD文件夹里创建文件，封装操作数据库的方法
# 4.在路由处理函数里面调用CRUD封装好的方法，响应结果

# 获取新闻分类列表
@router.get("/categories")
async def get_categories(
    skip: int = 0, 
    limit: int = 100,
    db: AsyncSession = Depends(db_config.get_database)
):
    """先获取数据库里面的新闻分类数据 -》定义模型类 -》封装调用方法"""
    categories =  await news.get_categories(db, skip=skip, limit=limit)
    return {
        "code": 200,
        "message": "success",
        "data": categories
    }

# 获取新闻列表
@router.get("/list")
async def get_news_list(
    category_id: int = Query(..., description="分类ID", alias="categoryId"),
    page: int = 1, 
    page_size: int = Query(10, le=100, description="每页数量", alias="pageSize"),
    db: AsyncSession = Depends(db_config.get_database)
):
    """获取新闻列表数据 -》定义模型类 -》封装调用方法"""
    # 处理分页规则 查询新闻列表 计算总量 计算是否还有更多
    skip = (page - 1) * page_size
    news_list = await news.get_news_list(db, category_id, skip=skip, limit=page_size)
    total_count = await news.get_news_count(db, category_id)
    has_more = total_count > skip + page_size
    return {
        "code": 200,
        "message": "success",
        "data": {
            "list": news_list,
            "total": total_count, # 当前分类下的新闻总数
            "hasMore": has_more # 是否允许滑动加载更多
        }
    }

# 获取新闻详情
@router.get("/detail")
async def get_news_datail(
    news_id: int = Query(..., description="新闻ID", alias="id"),
    db: AsyncSession = Depends(db_config.get_database)
):
    result = await news.get_news_detail(db, news_id)
    if result is None:
        raise HTTPException(status_code=404, detail="News not found")
    
    views_res = await news.increase_news_views(db, news_id)
    if not views_res:
        raise HTTPException(status_code=404, detail="Failed to update views")

    related_news = await news.get_related_news(db, result.id, result.category_id)

    return {
        "code": 200,
        "message": "success",
        "data": {
            "id": result.id,
            "title": result.title,
            "content": result.content,
            "image": result.image,
            "author": result.author,
            "categoryId": result.category_id,
            "views": result.views,
            "publishTime": result.publish_time,
            "relatedNews": related_news
        }
    }

# 添加发表新闻功能
@router.post("/publish")
async def publish_news(
    data: NewsCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(db_config.get_database)
):
    news_item = await news.create_news(db, data, user.username, user.id)

    return success_response("发布新闻成功", news_item)

# 添加查看自己发布的新闻的功能
@router.get("/mine")
async def get_my_news(
    page: int = Query(1, ge=1,description="页码", alias="page"),
    page_size: int = Query(10, ge=1,le=100, description="每页数量", alias="pageSize"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(db_config.get_database)
):
    skip = (page - 1) * page_size
    my_news = await news.get_user_news_list(db, user.id, skip=skip, limit=page_size)
    total_count = await news.get_user_news_count(db, user.id)
    has_more = total_count > skip + page_size
    return success_response("获取新闻列表成功", {
        "list": my_news,
        "total": total_count,
        "hasMore": has_more
    })

# 添加编辑自己发布的新闻功能
@router.put("/update")
async def update_news(
    data: NewsUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(db_config.get_database)
):
    news_item = await news.update_news(db, data, user.id)
    return success_response("更新新闻成功", news_item)

# 添加删除自己发布的新闻功能
@router.delete("/delete/{news_id}")
async def delete_news(
    news_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(db_config.get_database)
):
    deleted_item = await news.delete_news(db, news_id, user.id)
    return success_response("删除新闻成功", deleted_item)
