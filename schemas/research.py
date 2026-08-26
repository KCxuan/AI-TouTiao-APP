from typing import Literal

from pydantic import BaseModel, Field


ReviewAction = Literal[
    "approve",
    "revise",
    "research_more",
    "change_goal",
]

ResearchStatus = Literal[
    "waiting_review",
    "completed",
]


class ResearchStartRequest(BaseModel):
    """发起新闻研究时的请求体。"""

    user_input: str = Field(
        ...,
        min_length=1,
        description="用户输入的新闻研究主题",
    )


class ResearchReviewRequest(BaseModel):
    """用户审核研究报告草稿时的请求体。"""

    action: ReviewAction = Field(
        ...,
        description="用户对研究报告草稿的操作",
    )

    feedback: str | None = Field(
        default=None,
        description="修改意见、补查方向或新的研究目标",
    )


class ResearchResult(BaseModel):
    """Research Service 返回给 Router 的统一结果。"""

    thread_id: str
    status: ResearchStatus

    instruction: str | None = None
    draft_report: str | None = None
    final_report: str | None = None

    search_round: int | None = None
    hard_max_search_rounds: int | None = None

    allowed_actions: list[ReviewAction] = Field(
        default_factory=list,
    )