from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_config import get_database
from models.users import User
from schemas.chat import ChatRequest
from services.chat_service import (
    clear_chat_history_for_user,
    get_chat_history_for_user,
    reply_and_persist_chat,
)
from utils.auth import get_current_user
from utils.response import success_response

router = APIRouter(
    prefix="/api/ai",
    tags=["AI Chat"],
)


@router.get("/chat/history")
async def get_chat_history(
    limit: int = Query(20, ge=1, le=50, description="恢复的最近问答轮数"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database),
):
    result = await get_chat_history_for_user(user.id, limit, db)
    return success_response(
        message="已获取最近对话",
        data=result,
    )


@router.delete("/chat/history")
async def clear_chat_history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database),
):
    deleted = await clear_chat_history_for_user(user.id, db)
    return success_response(
        message="对话记录已清空",
        data={"cleared": deleted},
    )


@router.post("/chat")
async def chat_with_ai(
    data: ChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database),
):
    result = await reply_and_persist_chat(
        user_id=user.id,
        message=data.message,
        history=data.history,
        db=db,
    )
    return success_response(
        message="对话成功",
        data=result,
    )