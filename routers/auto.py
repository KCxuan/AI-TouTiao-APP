from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_config import get_database
from models.users import User
from schemas.auto import AutoRequest
from services.auto_service import handle_auto_request
from services.research_service import start_research_for_user
from utils.auth import get_current_user
from utils.response import success_response

router = APIRouter(
    prefix="/api/ai",
    tags=["AI Auto"],
)


@router.post("/auto")
async def use_auto_mode(
    data: AutoRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database),
):
    import asyncio

    result = await asyncio.to_thread(
        handle_auto_request,
        data.message,
        data.history,
    )

    if result.selected_mode == "research":
        result.research_result = await start_research_for_user(
            user_id=user.id,
            user_input=data.message,
            db=db,
        )

    message = {
        "chat": "已使用普通对话模式",
        "research": "已启动深度研究模式",
        "clarify": "需要补充信息",
    }[result.selected_mode]

    return success_response(
        message=message,
        data=result,
    )