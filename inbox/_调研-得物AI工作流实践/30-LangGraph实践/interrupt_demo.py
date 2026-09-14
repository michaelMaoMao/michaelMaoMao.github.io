"""
LangGraph interrupt/resume 最小落地 demo
验证得物活动搭建「6 中断点 + 中断恢复」的核心机制。

不调真 LLM（parse_node 用固定草稿替代），纯验证：
1. 图跑到 confirm 节点会 interrupt 暂停
2. Checkpointer 持久化状态（同 thread_id 可恢复）
3. Command(resume=...) 从断点继续到 build

对应文档库：30-LangGraph实践/LangGraph核心机制与代码.md (Phase 1 骨架)
"""
from typing import TypedDict
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class State(TypedDict):
    draft: str
    confirmed: dict
    result: str


def parse_node(state: State):
    """模拟 LLM 解析（模型只做语义感知）。真实场景这里调 llm_parse。"""
    print("  [parse] 生成草稿（模拟 LLM）")
    return {"draft": "这是 AI 生成的活动方案草稿"}


def confirm_node(state: State):
    """HITL 中断点：请求人工确认。interrupt() 暂停图，value 推给前端。"""
    print("  [confirm] 请求人工确认 ↓")
    feedback = interrupt({"draft": state["draft"], "msg": "请确认或修改"})
    print(f"  [confirm] 收到人工反馈: {feedback}")
    return {"confirmed": feedback}


def build_node(state: State):
    """写操作（确定性代码，放在确认之后 = 副作用延后原则）。"""
    print("  [build] 执行写操作（确认后才写，无脏数据）")
    return {"result": f"已构建会场: {state['confirmed']}"}


# 编译图（关键：checkpointer 持久化）
graph = (
    StateGraph(State)
    .add_node("parse", parse_node)
    .add_node("confirm", confirm_node)
    .add_node("build", build_node)
    .add_edge(START, "parse")
    .add_edge("parse", "confirm")
    .add_edge("confirm", "build")
    .add_edge("build", END)
    .compile(checkpointer=InMemorySaver())
)


def main():
    config = {"configurable": {"thread_id": "demo-session-1"}}

    print("=" * 50)
    print("第 1 轮：跑到 confirm，预期在此 interrupt")
    print("=" * 50)
    for chunk in graph.stream({"draft": "", "confirmed": {}, "result": ""}, config):
        print("  chunk:", chunk)

    # 检查中断状态
    state = graph.get_state(config)
    print("\n--- 中断状态 ---")
    print("  next (暂停在):", state.next)
    print("  已执行 values:", state.values)

    print("\n" + "=" * 50)
    print("第 2 轮：Command(resume=...) 恢复，预期跑到 build 结束")
    print("=" * 50)
    for chunk in graph.stream(
        Command(resume={"approved": True, "edited": "用户修改后的方案"}),
        config,
    ):
        print("  chunk:", chunk)

    print("\n--- 最终状态 ---")
    print(" ", graph.get_state(config).values)
    print("\n✓ interrupt/resume + checkpointer 验证通过")


if __name__ == "__main__":
    main()
