from pydantic import BaseModel, Field
from typing import Literal

from new_research_agent.llm import model

class ResearchPlan(BaseModel):
    """LLM 对用户研究请求的结构化分析结果。"""

    research_goal: str = Field(
        description="明确、具体的一句话研究目标"
    )

    research_questions: list[str] = Field(
        description="三个互不重复的研究问题"
    )

    current_query: str = Field(
        description=(
            "给站外新闻搜索用的一句自然语言查询，"
            "例如「C919飞机发展历程 国产大飞机」"
        )
    )

    internal_keywords: list[str] = Field(
        min_length=1,
        max_length=5,
        description=(
            "给站内标题/摘要 LIKE 用的实体短词，"
            "如产品名、机构名、人名、地名；"
            "不要「发展」「历程」「研究」这类抽象词"
        )
    )


class EvidenceAssessment(BaseModel):
    """LLM 对当前新闻摘要集合的审查结果。"""

    evidence_status: Literal[
        "sufficient",
        "insufficient",
    ] = Field(
        description="当前材料是否足以支持报告"
    )

    evidence_gaps: list[str] = Field(
        description="当前材料仍然缺少的信息"
    )

    source_conflicts: list[str] = Field(
        description="不同来源之间明确存在的冲突"
    )

    next_query: str | None = Field(
        description=(
            "证据不足时的下一条搜索词；"
            "证据充分时为 null"
        )
    )






research_planner = model.with_structured_output(
    ResearchPlan,

    # DeepSeek Chat Completions 支持 JSON Object，
    # 因此这里不要使用默认的 json_schema。
    method="json_mode",
)

evidence_reviewer = model.with_structured_output(
    EvidenceAssessment,
    method="json_mode",
)