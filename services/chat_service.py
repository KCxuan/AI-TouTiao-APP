import asyncio

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from sqlalchemy.ext.asyncio import AsyncSession

from crud.chat import (
    clear_ai_chats,
    create_ai_chat,
    list_recent_ai_chats,
)
from new_research_agent.llm import model
from schemas.chat import (
    ChatHistoryResult,
    ChatMessage,
    ChatResult,
    ChatTurn,
)


SYSTEM_PROMPT = """
你是“头条新闻”应用的 AI 助手。

请使用简体中文回答，语气友好、清晰、简洁。
你可以回答常识问题、解释概念、总结用户提供的内容，
也可以进行普通的交流和讨论。

当前是普通对话模式，不会调用新闻搜索工具。
如果用户询问近期新闻、实时变化、多来源对比，
或者要求提供可追溯的新闻证据，
请建议用户使用深度研究模式。
""".strip()


def generate_chat_reply(
    message: str,
    history: list[ChatMessage],
) -> ChatResult:
    """根据短期对话历史生成一次普通回复。"""

    model_messages: list[BaseMessage] = [
        SystemMessage(
            content=SYSTEM_PROMPT,
        ),
    ]

    for item in history[-20:]:
        if item.role == "user":
            model_messages.append(
                HumanMessage(
                    content=item.content
                )
            )
        else:
            model_messages.append(
                AIMessage(
                    content=item.content
                )
            )

    model_messages.append(
        HumanMessage(
            content=message
        )
    )

    response = model.invoke(
        model_messages,
    )

    if not isinstance(
        response.content,
        str,
    ):
        raise ValueError(
            "对话模型必须返回文本内容。"
        )

    return ChatResult(
        answer=response.content.strip(),
    )


async def reply_and_persist_chat(
    user_id: int,
    message: str,
    history: list[ChatMessage],
    db: AsyncSession,
) -> ChatResult:
    """生成回复；仅 Chat 模式写入 ai_chat。落库失败不影响返回。"""

    result = await asyncio.to_thread(
        generate_chat_reply,
        message,
        history,
    )

    try:
        await create_ai_chat(
            user_id=user_id,
            message=message,
            response=result.answer,
            db=db,
        )
    except Exception as exc:
        print(f"保存对话失败，仍返回本次回答：{exc}")
        await db.rollback()

    return result


async def get_chat_history_for_user(
    user_id: int,
    limit: int,
    db: AsyncSession,
) -> ChatHistoryResult:
    rows = await list_recent_ai_chats(user_id, limit, db)
    return ChatHistoryResult(
        list=[
            ChatTurn(
                id=row.id,
                message=row.message,
                response=row.response,
                created_at=row.created_at,
            )
            for row in rows
        ]
    )


async def clear_chat_history_for_user(
    user_id: int,
    db: AsyncSession,
) -> int:
    return await clear_ai_chats(user_id, db)