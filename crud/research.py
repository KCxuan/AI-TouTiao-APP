from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.research import ResearchRun


async def abandon_waiting_runs(user_id: int, db: AsyncSession) -> int:
    """同一用户只保留一份待审核任务，新研究开始前放弃旧草稿。"""
    stmt = (
        update(ResearchRun)
        .where(
            ResearchRun.user_id == user_id,
            ResearchRun.status == "waiting_review",
        )
        .values(status="abandoned")
    )
    result = await db.execute(stmt)
    await db.flush()
    return result.rowcount or 0


async def create_research_run(
    user_id: int,
    thread_id: str,
    user_input: str,
    status: str,
    db: AsyncSession,
) -> ResearchRun:
    run = ResearchRun(
        user_id=user_id,
        thread_id=thread_id,
        user_input=user_input,
        status=status,
    )
    db.add(run)
    await db.flush()
    await db.refresh(run)
    return run


async def update_research_run_status(
    thread_id: str,
    status: str,
    db: AsyncSession,
) -> None:
    stmt = (
        update(ResearchRun)
        .where(ResearchRun.thread_id == thread_id)
        .values(status=status)
    )
    await db.execute(stmt)
    await db.flush()


async def get_waiting_run(
    user_id: int,
    db: AsyncSession,
) -> ResearchRun | None:
    stmt = (
        select(ResearchRun)
        .where(
            ResearchRun.user_id == user_id,
            ResearchRun.status == "waiting_review",
        )
        .order_by(ResearchRun.updated_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalars().one_or_none()


async def get_run_for_user(
    thread_id: str,
    user_id: int,
    db: AsyncSession,
) -> ResearchRun | None:
    stmt = select(ResearchRun).where(
        ResearchRun.thread_id == thread_id,
        ResearchRun.user_id == user_id,
    )
    result = await db.execute(stmt)
    return result.scalars().one_or_none()


async def get_latest_completed_run(
    user_id: int,
    db: AsyncSession,
) -> ResearchRun | None:
    stmt = (
        select(ResearchRun)
        .where(
            ResearchRun.user_id == user_id,
            ResearchRun.status == "completed",
        )
        .order_by(ResearchRun.updated_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalars().one_or_none()


async def abandon_visible_runs(user_id: int, db: AsyncSession) -> int:
    """清空页面时：待审核和已完成都不再恢复。"""
    stmt = (
        update(ResearchRun)
        .where(
            ResearchRun.user_id == user_id,
            ResearchRun.status.in_(["waiting_review", "completed"]),
        )
        .values(status="abandoned")
    )
    result = await db.execute(stmt)
    await db.flush()
    return result.rowcount or 0