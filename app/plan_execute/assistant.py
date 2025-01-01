from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Annotated, Tuple
import operator
from app.plan_execute.planner import planner, re_planner
from executor import  agent_executor
from planner import Response
from langchain_core.messages import HumanMessage

class PlanExecute(TypedDict):
    input: str
    plan: List[str]
    past_steps: Annotated[List[Tuple], operator.add]
    response: str


async def plan_step(state: PlanExecute):
    plan = await planner.ainvoke({"objective": state["input"]})
    return {"plan": plan.steps}

async def execute_step(state: PlanExecute):
    task = state["plan"][0]
    messages = [HumanMessage(content=task)]
    agent_response = await agent_executor.ainvoke({"messages": messages})
    agent_response = agent_response["messages"][-1].content
    return {
        "past_steps": (task, agent_response)
    }

async def re_plan_step(state: PlanExecute):
    output = await re_planner.ainvoke(state)
    if isinstance(output, Response):
        return {"response": output.response}
    else:
        return {"plan": output.steps}

def should_end(state: PlanExecute):
    if state["response"]:
        return True
    else:
        return False


workflow = StateGraph(PlanExecute)

workflow.add_node("planner", plan_step)

workflow.add_node("executor", execute_step)

workflow.add_node("re_plan", re_plan_step)


workflow.set_entry_point("planner")

workflow.add_edge("planner", "executor")

workflow.add_edge("executor", "re_plan")

workflow.add_conditional_edges("re_plan", should_end, {True: END, False: "executor"})

agent = workflow.compile()

config = {"recursion_limit": 50}

inputs = {"input": "what is the home town of the 2024 Australia open winner?"}



# Display graph
image_data = agent.get_graph().draw_mermaid_png()

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

graph_image = resources_dir / "plan_execute.png"  # Creates an absolute path to the file

with open(graph_image, "wb") as f:
    f.write(image_data)

from PIL import Image as PILImage

img = PILImage.open("resources/plan_execute.png")
img.show()


# Wrap the async logic in an async function
async def run_agent():
    async for event in agent.astream(inputs, config=config):
        for k, v in event.items():
            if k != "__end__":
                print(v)


# Call the async function using asyncio
import asyncio

asyncio.run(run_agent())


