from fastapi import APIRouter, Depends, Query, HTTPException
from config.db_config import get_database
from sqlalchemy.ext.asyncio import AsyncSession
from models.users import User
from utils.response import success_response
from schemas.history import HistoryAddRequest, HistoryListResponse
from crud.history import add_history, get_history_list, remove_history_record, clear_history_list
from utils.auth import get_current_user


router = APIRouter(prefix="/api/history", tags=["history"])

# 添加浏览历史
@router.post("/add")
async def add_news_history(
    data: HistoryAddRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database),
):
    result = await add_history(user.id, data.news_id, db)
    return success_response(message="添加浏览历史成功", data=result) # 前端不响应具体新闻内容，直接返回也没关系 就是简单地返回一个成功信息 具体信息到后面获取浏览历史列表的时候再写


# 获取浏览历史列表
@router.get("/list")
async def get_news_history_list(
    page: int = Query(1, ge=1,description="页码", alias="page"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量", alias="pageSize"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database)
):
    rows, total = await get_history_list(page, page_size, user.id, db)
    history_list = [{
        **news.__dict__,
        "view_time": view_time,
        "history_id": history_id,
    } for news, view_time,history_id in rows]
    has_more = total > page * page_size
    data = HistoryListResponse(list=history_list, total=total, has_more=has_more)
    return success_response(message="获取浏览历史列表成功", data=data)

# 删除单条浏览记录
@router.delete("/delete/{history_id}")
async def delete_history(
    history_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database)
):
    result = await remove_history_record(history_id, user.id, db)
    if result:
        return success_response(message="删除浏览记录成功")
    else:
        raise HTTPException(status_code=404, detail="浏览记录不存在")


# 清空历史浏览列表
@router.delete("/clear")
async def clear_history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database)
):
    result = await clear_history_list(user.id, db)
    return success_response(message=f"清空历史浏览列表成功,一共{result}条记录")
