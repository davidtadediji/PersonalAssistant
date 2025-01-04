from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.types import interrupt
from app.llm_compiler.joiner import joiner
from app.llm_compiler.task_fetching_unit import plan_and_schedule


class State(TypedDict):
    messages: Annotated[list, add_messages]


def should_continue(state):
    messages = state["messages"]
    if isinstance(messages[-1], AIMessage):
        return END
    return "plan_and_schedule"

def human_node(state: State):
    value = interrupt(f"What should I say in response to {state['messages']}")
    return {"messages": [{"role": "assistant", "content": value}]}

graph_builder = StateGraph(State)

# Assign each node to a state variable to update
graph_builder.add_node("plan_and_schedule", plan_and_schedule)
graph_builder.add_node("join", joiner)

## Define edges
graph_builder.add_edge(START, "plan_and_schedule")
graph_builder.add_edge("plan_and_schedule", "join")
graph_builder.add_conditional_edges(
    "join",
    # Next, we pass in the function that will determine which node is called next.
    should_continue,
)
chain = graph_builder.compile()

# Graph visualization code
from pathlib import Path

project_root = Path(__file__).resolve().parent
resources_dir = project_root / "../../resources"
resources_dir.mkdir(parents=True, exist_ok=True)
graph_image = resources_dir / "llm_compiler.png"

image_data = chain.get_graph().draw_mermaid_png()
with open(graph_image, "wb") as f:
    f.write(image_data)

from PIL import Image as PILImage

img = PILImage.open(resources_dir / "llm_compiler.png")
img.show()


# for s in chain.stream(
#     {
#         "messages": [
#             HumanMessage(content="How are you")
#         ]
#     },
#     {"recursion_limit": 10},
# ):
#     if "__end__" in s:
#         print(s)
#         print("----")


def query_agent(query: str):
    last_msg = ""
    for msg in chain.stream(
        {"messages": [HumanMessage(content=query)]}, stream_mode="messages"
    ):
        last_msg = msg[0] if isinstance(msg, tuple) else msg
    return last_msg.content
