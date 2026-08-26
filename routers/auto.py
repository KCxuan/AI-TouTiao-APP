from fastapi import APIRouter

from schemas.auto import AutoRequest
from services.auto_service import (
    handle_auto_request,
)
from utils.response import success_response


router = APIRouter(
    prefix="/api/ai",
    tags=["AI Auto"],
)


@router.post("/auto")
def use_auto_mode(
    data: AutoRequest,
):
    """自动判断并进入合适的处理模式。"""

    result = handle_auto_request(
        message=data.message,
        history=data.history,
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