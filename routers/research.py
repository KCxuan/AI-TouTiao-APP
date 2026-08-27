from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_config import get_database
from models.users import User
from schemas.research import (
    ResearchReviewRequest,
    ResearchStartRequest,
)
from services.research_service import (
    get_current_research_for_user,
    review_research_for_user,
    start_research_for_user,
    clear_research_for_user,
)
from utils.auth import get_current_user
from utils.response import success_response

router = APIRouter(
    prefix="/api/ai/research",
    tags=["AI Research"],
)


@router.get("/current")
async def get_current_research(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database),
):
    """
    当前没有可以显示的研究
    """
    result = await get_current_research_for_user(user.id, db)
    if result is None:
        return success_response(
            message="当前没有待审核的研究",
            data=None,
        )
    return success_response(
        message="已恢复待审核的研究报告",
        data=result,
    )

@router.delete("/current")
async def clear_current_research(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database),
):
    """
    清空当前的研究报告记录
    """
    deleted = await clear_research_for_user(user.id, db)
    return success_response(
        message="研究记录已清空",
        data={"cleared": deleted},
    )


@router.post("/start")
async def start_news_research(
    data: ResearchStartRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database),
):
    """
    启动新闻研究，生成研究报告草稿
    """
    result = await start_research_for_user(
        user_id=user.id,
        user_input=data.user_input,
        db=db,
    )
    return success_response(
        message="研究报告草稿已生成",
        data=result,
    )


@router.post("/{thread_id}/review")
async def submit_research_review(
    thread_id: str,
    data: ResearchReviewRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database),
):
    """
    提交研究报告审核，审核通过后生成最终研究报告, 审核不通过则返回修改意见
    """
    result = await review_research_for_user(
        user_id=user.id,
        thread_id=thread_id,
        action=data.action,
        feedback=data.feedback,
        db=db,
    )
    message = (
        "研究报告已完成"
        if result.status == "completed"
        else "研究报告草稿已更新"
    )
    return success_response(
        message=message,
        data=result,
    )