from fastapi import APIRouter

from schemas.chat import ChatRequest
from services.chat_service import (
    generate_chat_reply,
)
from utils.response import success_response


router = APIRouter(
    prefix="/api/ai",
    tags=["AI Chat"],
)


@router.post("/chat")
def chat_with_ai(
    data: ChatRequest,
):
    """进行一次普通 AI 对话。"""

    result = generate_chat_reply(
        message=data.message,
        history=data.history,
    )

    return success_response(
        message="对话成功",
        data=result,
    )