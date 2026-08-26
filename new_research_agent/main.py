from uuid import uuid4

from langgraph.types import Command

from new_research_agent.agentstate import ResearchState
from new_research_agent.graph import research_graph


def create_initial_state(
    user_input: str,
) -> ResearchState:
    """创建一次研究任务的初始状态。"""

    return {
        "user_input": user_input,
        "used_queries": [],
        "sources": [],
        "search_round": 0,
        "max_search_rounds": 3,
        "hard_max_search_rounds": 5,
        "evidence_status": "unchecked",
        "evidence_gaps": [],
        "source_conflicts": [],
        "review_action": None,
        "review_feedback": None,
    }


def ask_user_to_review(
    review_request: dict,
) -> dict[str, str | None]:
    """展示草稿，并获取用户审核结果。"""

    print()
    print("=" * 60)
    print("报告草稿等待审核")
    print("=" * 60)
    print(review_request["draft_report"])

    print(
        "\n搜索轮数："
        f"{review_request['search_round']}"
        " / "
        f"{review_request['hard_max_search_rounds']}"
    )

    allowed_actions = review_request[
        "allowed_actions"
    ]

    while True:
        print(
            "可选操作："
            + " / ".join(allowed_actions)
        )

        action = input(
            "请输入审核操作："
        ).strip().lower()

        if action not in allowed_actions:
            print("请输入上面列出的操作。")
            continue

        if action == "approve":
            return {
                "action": "approve",
                "feedback": None,
            }

        if action == "research_more":
            feedback = input(
                "希望补查什么？可以直接回车："
            ).strip()

            return {
                "action": "research_more",
                "feedback": feedback or None,
            }

        if action == "revise":
            prompt = "请输入报告修改意见："
        else:
            prompt = "请输入新的研究方向："

        feedback = input(prompt).strip()

        if not feedback:
            print("这里不能为空。")
            continue

        return {
            "action": action,
            "feedback": feedback,
        }


def main() -> None:
    """运行带人工审核的新闻研究 Agent。"""

    user_input = input(
        "请输入新闻研究主题："
    ).strip()

    if not user_input:
        print("研究主题不能为空。")
        return

    initial_state = create_initial_state(
        user_input=user_input,
    )

    # 每次启动程序都创建一个独立任务编号。
    thread_id = str(uuid4())

    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    print()
    print("开始执行新闻研究 Agent……")
    print(f"当前任务 thread_id：{thread_id}")

    # 第一次执行：从 START 开始，直到 interrupt() 暂停。
    result = research_graph.invoke(
        initial_state,
        config=config,
    )

    while True:
        interrupts = result.get(
            "__interrupt__",
            (),
        )

        # 没有中断，说明图已经执行到 END。
        if not interrupts:
            final_report = result.get(
                "final_report"
            )

            print()
            print("=" * 60)
            print("研究任务执行完成")
            print("=" * 60)

            if final_report:
                print(final_report)
            else:
                print("流程结束，但没有生成最终报告。")

            return

        # 取出 interrupt() 传给外部的审核内容。
        review_request = interrupts[0].value

        review_response = ask_user_to_review(
            review_request
        )

        # 使用同一个 thread_id 恢复原任务。
        result = research_graph.invoke(
            Command(
                resume=review_response,
            ),
            config=config,
        )


if __name__ == "__main__":
    main()