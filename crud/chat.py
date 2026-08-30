from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.chat import AIChat


async def create_ai_chat(
    user_id: int,
    message: str,
    response: str,
    db: AsyncSession,
) -> AIChat:
    record = AIChat(
        user_id=user_id,
        message=message,
        response=response,
    )
    db.add(record)
    await db.flush()
    await db.refresh(record)
    return record


async def list_recent_ai_chats(
    user_id: int,
    limit: int,
    db: AsyncSession,
) -> list[AIChat]:
    query = (
        select(AIChat)
        .where(AIChat.user_id == user_id)
        .order_by(AIChat.id.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    rows = list(result.scalars().all())
    rows.reverse()
    return rows


async def clear_ai_chats(user_id: int, db: AsyncSession) -> int:
    stmt = delete(AIChat).where(AIChat.user_id == user_id)
    result = await db.execute(stmt)
    return result.rowcount or 0