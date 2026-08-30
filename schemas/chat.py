from typing import Literal

from pydantic import BaseModel, Field


ChatRole = Literal[
    "user",
    "assistant",
]


class ChatMessage(BaseModel):
    """一条已经完成的历史消息。"""

    role: ChatRole

    content: str = Field(
        ...,
        min_length=1,
        description="历史消息内容",
    )


class ChatRequest(BaseModel):
    """普通对话请求。"""

    message: str = Field(
        ...,
        min_length=1,
        description="用户本次发送的消息",
    )

    history: list[ChatMessage] = Field(
        default_factory=list,
        description="本次消息之前的短期对话历史",
    )


class ChatResult(BaseModel):
    """普通对话结果。"""

    answer: str


from datetime import datetime


class ChatTurn(BaseModel):
    """数据库中的一轮问答。"""

    id: int
    message: str
    response: str
    created_at: datetime


class ChatHistoryResult(BaseModel):
    """进入页面时恢复的最近对话。"""

    list: list[ChatTurn]