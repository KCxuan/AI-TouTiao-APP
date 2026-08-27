import asyncio
from typing import Any
from uuid import uuid4

from fastapi import HTTPException
from langgraph.types import Command
from sqlalchemy.ext.asyncio import AsyncSession

from crud.research import (
    abandon_waiting_runs,
    create_research_run,
    get_run_for_user,
    get_waiting_run,
    update_research_run_status,
    get_latest_completed_run,
    abandon_visible_runs,
)
from new_research_agent.graph import research_graph
from new_research_agent.main import create_initial_state
from schemas.research import ResearchResult, ReviewAction


def _build_config(thread_id: str) -> dict:
    return {
        "configurable": {
            "thread_id": thread_id,
        }
    }


def _get_interrupt_payload(snapshot: Any) -> dict[str, Any] | None:
    """兼容不同 LangGraph 版本读取 interrupt 内容。"""
    interrupts = getattr(snapshot, "interrupts", None) or ()
    if interrupts:
        first = interrupts[0]
        value = getattr(first, "value", first)
        return value if isinstance(value, dict) else None

    for task in getattr(snapshot, "tasks", ()) or ():
        task_interrupts = getattr(task, "interrupts", ()) or ()
        if task_interrupts:
            first = task_interrupts[0]
            value = getattr(first, "value", None)
            return value if isinstance(value, dict) else None

    return None


def _build_research_result(
    thread_id: str,
    graph_result: dict[str, Any],
    user_input: str | None = None,
) -> ResearchResult:
    interrupts = graph_result.get("__interrupt__", ())

    if interrupts:
        review_request = interrupts[0].value
        return ResearchResult(
            thread_id=thread_id,
            status="waiting_review",
            user_input=user_input,
            instruction=review_request["instruction"],
            draft_report=review_request["draft_report"],
            search_round=review_request["search_round"],
            hard_max_search_rounds=review_request["hard_max_search_rounds"],
            allowed_actions=review_request["allowed_actions"],
        )

    return ResearchResult(
        thread_id=thread_id,
        status="completed",
        user_input=user_input,
        final_report=graph_result["final_report"],
    )


def _load_result_from_checkpoint(
    thread_id: str,
    user_input: str | None = None,
) -> ResearchResult | None:
    snapshot = research_graph.get_state(_build_config(thread_id))
    payload = _get_interrupt_payload(snapshot)

    if payload:
        # 如果还停在审核状态，则返回等待审核状态
        return ResearchResult(
            thread_id=thread_id,
            status="waiting_review",
            user_input=user_input,
            instruction=payload.get("instruction"),
            draft_report=payload.get("draft_report"),
            search_round=payload.get("search_round"),
            hard_max_search_rounds=payload.get(
                "hard_max_search_rounds"
            ),
            allowed_actions=payload.get("allowed_actions") or [],
        )

    values = snapshot.values or {}
    final_report = values.get("final_report")
    if final_report:
        return ResearchResult(
            thread_id=thread_id,
            status="completed",
            user_input=user_input,
            final_report=final_report,
        )

    return None


def _invoke_new_research(user_input: str) -> ResearchResult:
    thread_id = str(uuid4())
    graph_result = research_graph.invoke(
        create_initial_state(user_input=user_input),
        config=_build_config(thread_id),
    )
    return _build_research_result(thread_id, graph_result, user_input)


def _invoke_review(
    thread_id: str,
    action: ReviewAction,
    feedback: str | None,
    user_input: str | None,
) -> ResearchResult:
    graph_result = research_graph.invoke(
        Command(
            resume={
                "action": action,
                "feedback": feedback,
            }
        ),
        config=_build_config(thread_id),
    )
    return _build_research_result(thread_id, graph_result, user_input)


async def start_research_for_user(
    user_id: int,
    user_input: str,
    db: AsyncSession,
) -> ResearchResult:
    """放弃旧的待审核任务，启动新研究并写入任务表。"""
    await abandon_waiting_runs(user_id, db)
    await db.commit()

    result = await asyncio.to_thread(_invoke_new_research, user_input)
    await create_research_run(
        user_id=user_id,
        thread_id=result.thread_id,
        user_input=user_input,
        status=result.status,
        db=db,
    )
    return result


async def review_research_for_user(
    user_id: int,
    thread_id: str,
    action: ReviewAction,
    feedback: str | None,
    db: AsyncSession,
) -> ResearchResult:
    run = await get_run_for_user(thread_id, user_id, db)
    if run is None:
        raise HTTPException(status_code=403, detail="无权审核该研究任务")
    if run.status != "waiting_review":
        raise HTTPException(status_code=409, detail="该研究任务不在待审核状态")

    result = await asyncio.to_thread(
        _invoke_review,
        thread_id,
        action,
        feedback,
        run.user_input,
    )
    await update_research_run_status(thread_id, result.status, db)
    return result


async def get_current_research_for_user(
    user_id: int,
    db: AsyncSession,
) -> ResearchResult | None:
    run = await get_waiting_run(user_id, db)
    if run is None:
        run = await get_latest_completed_run(user_id, db)
    if run is None:
        return None

    result = await asyncio.to_thread(
        _load_result_from_checkpoint,
        run.thread_id,
        run.user_input,
    )
    if result is None:
        await update_research_run_status(run.thread_id, "abandoned", db)
        return None
    return result


async def clear_research_for_user(
    user_id: int,
    db: AsyncSession,
) -> int:
    return await abandon_visible_runs(user_id, db)