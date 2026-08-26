from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from new_research_agent.agentstate import ResearchState
from new_research_agent.nodes import (
    analyze_research_goal,
    assess_evidence,
    search_news,
    finalize_report,
    generate_draft_report,
    human_review,
)
from new_research_agent.routes import (
    route_after_evidence,
    route_after_review,
)


def build_research_graph():
    """构建带人工审核的新闻研究图。"""

    builder = StateGraph(ResearchState)

    # 一、注册研究节点
    builder.add_node(
        "analyze_goal",
        analyze_research_goal,
    )
    builder.add_node(
        "search_news",
        search_news,
    )
    builder.add_node(
        "assess_evidence",
        assess_evidence,
    )
    builder.add_node(
        "generate_draft",
        generate_draft_report,
    )

    # 二、注册人工审核节点
    builder.add_node(
        "human_review",
        human_review,
    )
    builder.add_node(
        "finalize",
        finalize_report,
    )

    # 三、研究主流程
    builder.add_edge(
        START,
        "analyze_goal",
    )
    builder.add_edge(
        "analyze_goal",
        "search_news",
    )
    builder.add_edge(
        "search_news",
        "assess_evidence",
    )

    builder.add_conditional_edges(
        "assess_evidence",
        route_after_evidence,
        {
            "search_again": "search_news",
            "write_draft": "generate_draft",
        },
    )

    # 四、草稿生成后必须进入人工审核
    builder.add_edge(
        "generate_draft",
        "human_review",
    )

    # 五、根据用户审核结果分支
    builder.add_conditional_edges(
        "human_review",
        route_after_review,
        {
            "generate_draft": "generate_draft",
            "search_news": "search_news",
            "analyze_goal": "analyze_goal",
            "finalize": "finalize",
        },
    )

    # 只有定稿完成后才能结束
    builder.add_edge(
        "finalize",
        END,
    )

    # interrupt() 需要 checkpointer 保存暂停位置。
    checkpointer = InMemorySaver()

    return builder.compile(
        checkpointer=checkpointer,
    )


research_graph = build_research_graph()
