from typing import Literal

from new_research_agent.agentstate import ResearchState


EvidenceRoute = Literal[
    "search_again",
    "write_draft",
]


def route_after_evidence(
    state: ResearchState,
) -> EvidenceRoute:
    """
    根据证据状态和搜索轮数，决定下一步执行什么。

    返回 search_again：
        证据不足，并且还有搜索机会。

    返回 write_draft：
        证据已经充分；
        或者证据仍然不足，但已经达到最大搜索轮数。
    """
    evidence_status = state.get(
        "evidence_status",
        "unchecked",
    )
    search_round = state.get("search_round", 0)
    max_search_rounds = state["max_search_rounds"]

    # 证据充分，可以提前结束搜索。
    if evidence_status == "sufficient":
        return "write_draft"

    # 如果没有执行证据评估，说明图的连接可能有问题。
    if evidence_status != "insufficient":
        raise ValueError(
            "执行证据路由前，必须先完成证据评估。"
            f"当前状态：{evidence_status}"
        )

    # 证据不足，但还没有达到最大搜索轮数。
    if search_round < max_search_rounds:
        return "search_again"

    # 证据不足，并且已经达到最大轮数。
    # 不再搜索，而是生成“证据有限版报告”。
    return "write_draft"

ReviewRoute = Literal[
    "generate_draft",
    "search_news",
    "analyze_goal",
    "finalize",
]


def route_after_review(
    state: ResearchState,
) -> ReviewRoute:
    """根据用户审核结果决定下一节点。"""

    review_action = state["review_action"]

    if review_action == "approve":
        return "finalize"

    if review_action == "revise":
        return "generate_draft"

    if review_action == "research_more":
        return "search_news"

    if review_action == "change_goal":
        return "analyze_goal"

    raise ValueError(
        f"未知的审核操作：{review_action}"
    )