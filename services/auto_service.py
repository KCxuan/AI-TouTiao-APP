from new_research_agent.llm import model
from schemas.auto import (
    AutoResult,
    AutoRouteDecision,
)
from schemas.chat import ChatMessage
from services.chat_service import (
    generate_chat_reply,
)
from services.research_service import (
    start_research,
)


AUTO_ROUTE_PROMPT = """
你是“头条新闻”应用的模式分类器。

你的任务只是判断用户消息应该进入哪种模式，
不要回答用户的问题。

分类规则：

1. chat
适用于普通交流、概念解释、代码答疑、翻译改写、
总结用户已经提供的内容，以及不需要查询外部信息的问题。

2. research
适用于近期新闻、实时变化、多来源对比、事件时间线、
事实核查、要求引用来源，或者要求生成新闻研究报告的问题。

3. clarify
适用于研究对象或请求目标不明确，
当前无法形成清晰研究问题的情况。

不要因为消息中出现“新闻”两个字就一定选择 research。
如果用户只是询问新闻相关概念，仍然选择 chat。

必须返回下面格式的 JSON 对象：

{
  "route": "chat、research 或 clarify",
  "clarification_question": "需要澄清时的问题，否则为 null"
}
""".strip()


auto_classifier = model.with_structured_output(
    AutoRouteDecision,

    # 当前模型配置已经验证过 JSON Object。
    method="json_mode",
)


def classify_auto_route(
    message: str,
) -> AutoRouteDecision:
    """判断用户消息应该进入哪种模式。"""

    return auto_classifier.invoke(
        [
            (
                "system",
                AUTO_ROUTE_PROMPT,
            ),
            (
                "human",
                message,
            ),
        ]
    )


def handle_auto_request(
    message: str,
    history: list[ChatMessage],
) -> AutoResult:
    """判断模式，并把请求交给对应的 Service。"""

    decision = classify_auto_route(
        message,
    )

    if decision.route == "chat":
        chat_result = generate_chat_reply(
            message=message,
            history=history,
        )

        return AutoResult(
            selected_mode="chat",
            chat_result=chat_result,
        )

    if decision.route == "research":
        research_result = start_research(
            user_input=message,
        )

        return AutoResult(
            selected_mode="research",
            research_result=research_result,
        )

    return AutoResult(
        selected_mode="clarify",
        clarification_question=(
            decision.clarification_question
        ),
    )