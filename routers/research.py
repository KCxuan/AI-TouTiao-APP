from fastapi import APIRouter

from schemas.research import (
    ResearchReviewRequest,
    ResearchStartRequest,
)
from services.research_service import (
    review_research,
    start_research,
)
from utils.response import success_response


router = APIRouter(
    prefix="/api/ai/research",
    tags=["AI Research"],
)


@router.post("/start")
def start_news_research(
    data: ResearchStartRequest,
):
    """发起一次新的新闻研究任务。"""

    result = start_research(
        user_input=data.user_input,
    )

    return success_response(
        message="研究报告草稿已生成",
        data=result,
    )


@router.post("/{thread_id}/review")
def submit_research_review(
    thread_id: str,
    data: ResearchReviewRequest,
):
    """提交审核结果并恢复研究任务。"""

    result = review_research(
        thread_id=thread_id,
        action=data.action,
        feedback=data.feedback,
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