import os
from typing import Annotated
from typing import List

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph, START
from langgraph.graph.message import add_messages, RemoveMessage
from langgraph.pregel.retry import RetryPolicy
from langgraph.types import interrupt
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from src.assistant.planning.joiner import joiner
from src.assistant.planning.prompts import TOOL_CATEGORY_PROMPT
from src.assistant.planning.task_fetching_unit import plan_and_schedule
from src.assistant.tools.tool_categories import get_all_tool_summaries

# db_path = "state_db/example.db"
#
# conn = sqlite3.connect(db_path, check_same_thread=False)
# memory = SqliteSaver(conn)


class ToolCategoryResponse(TypedDict):
    required_categories: List[str]
    explanation: str


# Define the State class
class State(TypedDict):
    messages: Annotated[list, add_messages]
    selected_tool_categories: ToolCategoryResponse
    summary: str


llm = ChatOpenAI(model=os.getenv("OPENAI_PLANNING_MODEL"))
tool_category_selector = llm.with_structured_output(schema=ToolCategoryResponse)


class QueryForTools(BaseModel):
    """Generate a query for additional tools."""

    query: str = Field(..., description="Query for additional tools.")


def select_tool_categories(state: State):
    # Get the last user message
    last_user_message = state["messages"][-1]

    # Step 1: Convert tool categories to a JSON-compatible format
    tool_categories_json = get_all_tool_summaries()

    # Step 2: Format the prompt with the available tool categories and the user's query
    formatted_prompt = TOOL_CATEGORY_PROMPT.format(
        tool_categories=tool_categories_json
    )

    messages = [
        SystemMessage(
            content=formatted_prompt
        ),
        last_user_message
    ]

    # Step 3: Invoke the LLM to analyze the task and select tool categories
    response = tool_category_selector.invoke(messages)

    # Step 4: Parse the LLM response (assuming it returns valid JSON)
    try:
        tool_category_response: ToolCategoryResponse = response
    except Exception as e:
        raise ValueError(f"Failed to parse LLM response: {e}")

    # Step 5: Update the state with the selected categories and response
    state["selected_tool_categories"] = tool_category_response

    return state


def summarize_conversation(state: State):
    summary = state.get("summary", "")

    if summary:
        summary_message = (
            f"This is summary of the interaction to date: {summary}\n\n"
            "Extend the summary by taking into account the new messages above:"
        )

    else:
        summary_message = "Create a summary of the conversation above:"

    messages = state["messages"] + [HumanMessage(content=summary_message)]
    response = llm.invoke(messages)

    delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-2]]
    return {"summary": response.content, "messages": delete_messages}


def should_summarize(state: State):
    """Return the next node to execute."""

    messages = state["messages"]

    if len(messages) > 6:
        return "summarize_conversation"

    return END


def should_continue(state):
    messages = state["messages"]
    if isinstance(messages[-1], AIMessage):
        return END
    return "select_tool_categories"


def human_node(state: State):
    value = interrupt(state['messages'][-1])
    return {"messages": [{"role": "assistant", "content": value}]}


graph_builder = StateGraph(State)
graph_builder.add_node("select_tool_categories", select_tool_categories, retry=RetryPolicy(max_attempts=3))
# Assign each node to a state variable to update
graph_builder.add_node("plan_and_schedule", plan_and_schedule)
graph_builder.add_node("join", joiner)

## Define edges
graph_builder.add_edge(START, "select_tool_categories")
graph_builder.add_edge("select_tool_categories", "plan_and_schedule")
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
