from typing import TypedDict, List, Annotated, Tuple
import operator
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.graph import MessagesState
from langgraph.graph import StateGraph, START, END
from app.tools.functions import tavily_search, tavily_extract
from langchain_core.messages import HumanMessage

class Execute(TypedDict):
    input: str
    chat_history: List[str]
    agent_outcome: str

llm = ChatOpenAI(model="gpt-4o-mini")
tools = [tavily_search, tavily_extract]
llm_with_tools = llm.bind_tools(tools)

def tool_calling(state: MessagesState):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

builder = StateGraph(MessagesState)
builder.add_node("tool_calling", tool_calling)
builder.add_node("tools", ToolNode(tools))
builder.add_edge(START, "tool_calling")
builder.add_conditional_edges(
    "tool_calling",
    tools_condition
)

builder.add_edge("tools", "tool_calling")
agent_executor = builder.compile()

# messages = [HumanMessage(content="Who is the winner of the user open 2024")]
# messages = agent_executor.invoke({"messages": messages})
#
#
# for m in messages['messages']:
#     m.pretty_print()




# Display graph
image_data = agent_executor.get_graph().draw_mermaid_png()

# View

from pathlib import Path

# Get the absolute path to the project root or app directory
project_root = (
    Path(__file__).resolve().parent
)  # This is the directory where server.py is located
resources_dir = (
    project_root / "../resources"
)  # Use the / operator to join paths (pathlib feature)

# Ensure the resources directory exists
resources_dir.mkdir(parents=True, exist_ok=True)

graph_image = resources_dir / "executor.png"  # Creates an absolute path to the file

with open(graph_image, "wb") as f:
    f.write(image_data)

from PIL import Image as PILImage

img = PILImage.open("resources/executor.png")
img.show()