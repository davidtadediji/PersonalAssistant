from typing import Annotated, TypedDict, Union
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph, START
import os
from langgraph.prebuilt import tools_condition
from langgraph.graph.message import add_messages

from app.llm_compiler.joiner import joiner
from app.llm_compiler.planner import tools
from app.llm_compiler.task_fetching_unit import plan_and_schedule


class State(TypedDict):
    messages: Annotated[list, add_messages]


llm = ChatOpenAI(model=os.getenv("PLANNING_MODEL"))
llm_with_tools = llm.bind_tools(tools, parallel_tool_calls=False)


def evaluate_complexity(state):
    """Evaluates if the query needs planning and tools."""
    messages = state["messages"]
    evaluation_prompt = SystemMessage(content="""Evaluate if this query requires complex planning or tools. 
    Return 'needs_planning' if tools or complex planning are needed, 'direct_response' if a simple response is sufficient.
    Consider:
    - Does it require accessing external tools or data?
    - Does it need multiple steps or complex planning?
    - Can it be answered with just knowledge?""")

    evaluation = llm.invoke([evaluation_prompt] + messages)
    # Return the state with the original messages
    return {"messages": state["messages"]}


def route_based_on_evaluation(state):
    """Routes to the appropriate node based on evaluation."""
    messages = state["messages"]
    evaluation_prompt = SystemMessage(content="""Evaluate if this query requires complex planning or tools. 
    Return 'needs_planning' if tools or complex planning are needed, 'direct_response' if a simple response is sufficient.""")

    evaluation = llm.invoke([evaluation_prompt] + messages)
    if "needs_planning" in evaluation.content.lower():
        return "plan_and_schedule"
    return "direct_response"


def direct_response(state):
    """Handles simple queries that don't need planning."""
    messages = state["messages"]
    response = llm.invoke(messages)
    return {"messages": messages + [response]}


def call_node(state):
    """Handles complex queries that need planning."""
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": messages + [response]}


# Build the graph
graph_builder = StateGraph(State)

# Add nodes
graph_builder.add_node("evaluate", evaluate_complexity)
graph_builder.add_node("direct_response", direct_response)
graph_builder.add_node("plan_and_schedule", plan_and_schedule)
graph_builder.add_node("joiner", joiner)

# Add edges
graph_builder.add_edge(START, "evaluate")
graph_builder.add_conditional_edges(
    "evaluate",
    route_based_on_evaluation,
    {
        "direct_response": "direct_response",
        "plan_and_schedule": "plan_and_schedule"
    }
)
graph_builder.add_edge("direct_response", END)
graph_builder.add_edge("plan_and_schedule", "joiner")
graph_builder.add_conditional_edges(
    "joiner",
    lambda state: END if isinstance(state["messages"][-1], AIMessage) else "plan_and_schedule"
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

img = PILImage.open("../../resources/llm_compiler.png")
img.show()


for step in chain.stream(
    {"messages": [HumanMessage(content="How are you")]}
):
    print(step)
    print("---")

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
            {"messages": [HumanMessage(content=query)]}, stream_mode="messages"):
        last_msg = msg[0] if isinstance(msg, tuple) else msg
    return last_msg.content
