from fastapi import APIRouter, HTTPException
from crud import favorite
from utils.auth import get_current_user
from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from config.db_config import get_database
from models.users import User
from utils.response import success_response
from crud.favorite import is_news_favorite, add_favorite, remove_news_favorite, get_favorite_list, clear_favorite
from schemas.favorite import FavoriteCheckResponse, FavoriteAddRequest, FavoriteListResponse


router = APIRouter(prefix="/api/favorite", tags=["favorite"])

"""
检查新闻是否被收藏
"""
@router.get("/check")
async def check_favorite(
    news_id: int = Query(..., description="新闻ID", alias="newsId"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database),
):
    if not user:
        raise HTTPException(status_code=401, detail="用户未登录")

    is_favorited = await is_news_favorite(user.id, news_id, db)
    return success_response(
        message="检查收藏成功",
        data=FavoriteCheckResponse(is_favorite=is_favorited)
    )

"""
添加收藏
"""
@router.post("/add")
async def add_news_favorite(
    data: FavoriteAddRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database),
):
    result = await add_favorite(user.id, data.news_id, db)
    return success_response(message="添加收藏成功", data=result)# 前端不响应具体新闻内容，直接返回也没关系

"""
删除收藏
"""
@router.delete("/remove")
async def remove_favorite(
    news_id: int = Query(..., description="新闻ID", alias="newsId"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database),
):
    result = await remove_news_favorite(user.id, news_id, db)
    if result:
        return success_response(message="删除收藏成功")
    else:
        raise HTTPException(status_code=400, detail="没有收藏该新闻")

"""
获取收藏的新闻列表
"""
@router.get("/list")
async def get_news_favorite_list(
    page: int = Query(1, ge=1,description="页码", alias="page"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量", alias="pageSize"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database),
):
    rows, total = await get_favorite_list(user.id, page, page_size, db)
    favorite_list = [{
        **news.__dict__,
        "favorite_time": favorite_time,
        "favorite_id": favorite_id
    } for news, favorite_time, favorite_id in rows]
    has_more = total > page * page_size

    data = FavoriteListResponse(list=favorite_list, total=total, has_more=has_more)
    return success_response(message="获取收藏的新闻列表成功", data=data)

"""
清空收藏列表
"""
@router.delete("/clear")
async def clear_favorite(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database),
):
    result = await favorite.clear_favorite(user.id, db)
    return success_response(message=f"清空全部{result}条收藏成功")
