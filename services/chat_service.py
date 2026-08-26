from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)

from new_research_agent.llm import model
from schemas.chat import (
    ChatMessage,
    ChatResult,
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
                    content=item.content,
                )
            )
        else:
            model_messages.append(
                AIMessage(
                    content=item.content,
                )
            )

    model_messages.append(
        HumanMessage(
            content=message,
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