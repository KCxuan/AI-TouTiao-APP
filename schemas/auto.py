from typing import Literal

from pydantic import BaseModel, Field

from schemas.chat import (
    ChatMessage,
    ChatResult,
)
from schemas.research import ResearchResult


AutoMode = Literal[
    "chat",
    "research",
    "clarify",
]


class AutoRequest(BaseModel):
    """自动模式请求。"""

    message: str = Field(
        ...,
        min_length=1,
        description="用户本次发送的消息",
    )

    history: list[ChatMessage] = Field(
        default_factory=list,
        description="本次消息之前的短期对话历史",
    )


class AutoRouteDecision(BaseModel):
    """LLM 对用户消息的结构化分类结果。"""

    route: AutoMode = Field(
        description="消息应该进入的处理模式",
    )

    clarification_question: str | None = Field(
        description=(
            "route 为 clarify 时需要询问用户的问题；"
            "其他情况为 null"
        ),
    )


class AutoResult(BaseModel):
    """Auto Service 返回给 Router 的统一结果。"""

    selected_mode: AutoMode

    chat_result: ChatResult | None = None
    research_result: ResearchResult | None = None
    clarification_question: str | None = None