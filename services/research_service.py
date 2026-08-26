from typing import Any
from uuid import uuid4

from langgraph.types import Command

from new_research_agent.graph import research_graph
from new_research_agent.main import create_initial_state
from schemas.research import (
    ResearchResult,
    ReviewAction,
)


def _build_config(
    thread_id: str,
) -> dict:
    """构造 LangGraph 保存和恢复任务所需的配置。"""

    return {
        "configurable": {
            "thread_id": thread_id,
        }
    }


def _build_research_result(
    thread_id: str,
    graph_result: dict[str, Any],
) -> ResearchResult:
    """把 LangGraph 结果转换成接口容易使用的结果。"""

    interrupts = graph_result.get(
        "__interrupt__",
        (),
    )

    if interrupts:
        review_request = interrupts[0].value

        return ResearchResult(
            thread_id=thread_id,
            status="waiting_review",
            instruction=review_request[
                "instruction"
            ],
            draft_report=review_request[
                "draft_report"
            ],
            search_round=review_request[
                "search_round"
            ],
            hard_max_search_rounds=(
                review_request[
                    "hard_max_search_rounds"
                ]
            ),
            allowed_actions=review_request[
                "allowed_actions"
            ],
        )

    return ResearchResult(
        thread_id=thread_id,
        status="completed",
        final_report=graph_result[
            "final_report"
        ],
    )


def start_research(
    user_input: str,
) -> ResearchResult:
    """创建并启动一次新的新闻研究任务。"""

    thread_id = str(uuid4())

    graph_result = research_graph.invoke(
        create_initial_state(
            user_input=user_input,
        ),
        config=_build_config(thread_id),
    )

    return _build_research_result(
        thread_id,
        graph_result,
    )


def review_research(
    thread_id: str,
    action: ReviewAction,
    feedback: str | None,
) -> ResearchResult:
    """提交审核结果并恢复原来的研究任务。"""

    graph_result = research_graph.invoke(
        Command(
            resume={
                "action": action,
                "feedback": feedback,
            }
        ),
        config=_build_config(thread_id),
    )

    return _build_research_result(
        thread_id,
        graph_result,
    )