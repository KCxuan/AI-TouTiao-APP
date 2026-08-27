from operator import add
from typing import Annotated, Literal

from typing_extensions import TypedDict

class ResearchState(TypedDict, total=False):
    """新闻研究 Agent 在一次研究任务中的共享状态。"""

    # 一、用户输入与研究计划
    user_input: str
    research_goal: str
    research_questions: list[str]

    # 二、新闻搜索循环
    # 站外 Tavily 用的自然语言查询；每轮可更新。
    current_query: str
    # 站内 LIKE 用的实体短词；规划一次生成，后续轮次复用。
    internal_keywords: list[str]

    """
    # 使用 add reducer：
    # 每一轮产生的新搜索词会追加到旧列表，而不是覆盖旧列表。
    used_queries: Annotated[list[str], add]

    # 第一版暂时使用字典保存来源。
    # 接入真实 SearchTool 时再定义严格的 SearchResult 模型。
    sources: Annotated[
        list[dict[str, str | None]],
        add,
    ]
    """
    # 当前图是串行执行，由搜索节点显式累加。
    used_queries: list[str]

    sources: list[dict[str, str | None]]

    # 已完成的搜索轮数
    search_round: int

    # 最大允许搜索轮数
    max_search_rounds: int
    # 单个研究目标允许的绝对搜索上限，
    # 包括用户主动要求补查的轮数。
    hard_max_search_rounds: int

    # 三、证据充分性评估
    evidence_status: Literal[
        "unchecked",
        "sufficient",
        "insufficient",
    ]
    # 证据不足
    evidence_gaps: list[str]
    # 来源冲突
    source_conflicts: list[str]

    # 四、报告
    draft_report: str

    # 五、用户审核
    review_action: (
        Literal[
            "approve",
            "revise",
            "research_more",
            "change_goal",
        ]
        | None
    )
    review_feedback: str | None

    # 六、审核通过后的最终结果
    final_report: str