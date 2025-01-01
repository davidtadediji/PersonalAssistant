from langgraph.graph import END, StateGraph, START
from langgraph.graph.message import add_messages
from langchain_core.messages import AIMessage, HumanMessage
from typing import Annotated, TypedDict
from app.llm_compiler.joiner import joiner
from app.llm_compiler.task_fetching_unit import plan_and_schedule


class State(TypedDict):
    messages: Annotated[list, add_messages]

def should_continue(state):
    messages = state["messages"]
    if isinstance(messages[-1], AIMessage):
        return END
    return "plan_and_schedule"


graph_builder = StateGraph(State)
graph_builder.add_node("plan_and_schedule", plan_and_schedule)
graph_builder.add_node("joiner", joiner)

## Build workflow
graph_builder.add_edge("plan_and_schedule", "joiner")
graph_builder.add_conditional_edges(
    "joiner",
    # Next, we pass in the function that will determine which node is called next.
    should_continue,
)

graph_builder.add_edge(START, "plan_and_schedule")
chain = graph_builder.compile()


# Display graph
image_data = chain.get_graph().draw_mermaid_png()

# View

from pathlib import Path

# Get the absolute path to the project root or app directory
project_root = (
    Path(__file__).resolve().parent
)  # This is the directory where server.py is located
resources_dir = (
    project_root / "../../resources"
)  # Use the / operator to join paths (pathlib feature)

# Ensure the resources directory exists
resources_dir.mkdir(parents=True, exist_ok=True)

graph_image = resources_dir / "llm_compiler.png"  # Creates an absolute path to the file

with open(graph_image, "wb") as f:
    f.write(image_data)

from PIL import Image as PILImage

img = PILImage.open("../../resources/llm_compiler.png")
img.show()

for step in chain.stream(
    {"messages": [HumanMessage(content="what is the home town of the 2024 Australia open winner?")]}
):
    print(step)
    print("---")