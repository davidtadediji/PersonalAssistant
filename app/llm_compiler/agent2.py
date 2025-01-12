import uuid
from typing import Annotated

from langchain_core.documents import Document
from langchain_core.messages import AIMessage
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langgraph.graph import END
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.pregel.retry import RetryPolicy
from langgraph.types import interrupt
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from app.llm_compiler.joiner import joiner
from app.llm_compiler.task_fetching_unit import plan_and_schedule
from app.tools.location_information.current_location_tool import get_current_location_tool

tool_registry = {
    str(uuid.uuid4()): get_current_location_tool()
}

tool_documents = [
    Document(
        page_content=tool.description,
        id=tid,
        metadata={"tool_name": tool.name},
    )
    for tid, tool in tool_registry.items()
]

vector_store = InMemoryVectorStore(embedding=OpenAIEmbeddings())
document_ids = vector_store.add_documents(tool_documents)


# Define the state structure using TypedDict.
# It includes a list of messages (processed by add_messages)
# and a list of selected tool IDs.
class State(TypedDict):
    messages: Annotated[list, add_messages]
    selected_tools: list[str]


builder = StateGraph(State)

# Retrieve all available tools from the tool registry.
tools = list(tool_registry.values())
llm = ChatOpenAI()


# The agent function processes the current state
# by binding selected tools to the LLM.
def agent(state: State):
    # Map tool IDs to actual tools
    # based on the state's selected_tools list.
    selected_tools = [tool_registry[tid] for tid in state["selected_tools"]]
    # Bind the selected tools to the LLM for the current interaction.
    llm_with_tools = llm.bind_tools(selected_tools)
    # Invoke the LLM with the current messages and return the updated message list.
    return {"messages": [llm_with_tools.invoke(state["messages"])]}


class QueryForTools(BaseModel):
    """Generate a query for additional tools."""

    query: str = Field(..., description="Query for additional tools.")


def select_tools(state: State):
    """Selects tools based on the last message in the conversation state.

    If the last message is from a human, directly uses the content of the message
    as the query. Otherwise, constructs a query using a system message and invokes
    the LLM to generate tool suggestions.
    """
    last_message = state["messages"][-1]
    hack_remove_tool_condition = False  # Simulate an error in the first tool selection

    if isinstance(last_message, HumanMessage):
        query = last_message.content
        hack_remove_tool_condition = True  # Simulate wrong tool selection
    else:
        assert isinstance(last_message, ToolMessage)
        system = SystemMessage(
            "Given this conversation, generate a query for additional tools. "
            "The query should be a short string containing what type of information "
            "is needed. If no further information is needed, "
            "set more_information_needed False and populate a blank string for the query."
        )
        input_messages = [system] + state["messages"]
        response = llm.bind_tools([QueryForTools], tool_choice=True).invoke(
            input_messages
        )
        query = response.tool_calls[0]["args"]["query"]

    if hack_remove_tool_condition:
        # Simulate error by removing the correct tool from the selection
        selected_tools = [
            document.id
            for document in vector_store.similarity_search(query)
            if document.metadata["tool_name"] != "Advanced_Micro_Devices"
        ]
    else:
        selected_tools = [document.id for document in tool_documents]
    return {"selected_tools": selected_tools}


def should_continue(state):
    messages = state["messages"]
    if isinstance(messages[-1], AIMessage):
        return END
    return "plan_and_schedule"


def human_in_the_loop(state: State):
    value = interrupt(f"What should I say in response to {state['messages']}")
    return {"messages": [{"role": "assistant", "content": value}]}


graph_builder = StateGraph(State)
graph_builder.add_node("select_tools", select_tools, retry=RetryPolicy(max_attempts=3))
tool_node = ToolNode(tools=tools)
graph_builder.add_node("tools", tool_node)

# Assign each node to a state variable to update
graph_builder.add_node("plan_and_schedule", plan_and_schedule)
graph_builder.add_node("join", joiner)

## Define edges
graph_builder.add_edge(START, "select_tools")
graph_builder.add_edge("select_tools", "plan_and_schedule")
graph_builder.add_edge("plan_and_schedule", "join")
graph_builder.add_conditional_edges(
    "join",
    # Next, we pass in the function that will determine which node is called next.
    should_continue,
)
chain = graph_builder.compile()


def query_agent(query: str):
    last_msg = ""
    for msg in chain.stream(
            {"messages": [HumanMessage(content=query)]}, stream_mode="messages"
    ):
        last_msg = msg[0] if isinstance(msg, tuple) else msg
    return last_msg.content


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
