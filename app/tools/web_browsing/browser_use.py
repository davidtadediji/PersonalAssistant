import asyncio
from typing import Dict
from langchain_openai import ChatOpenAI
from browser_use import Agent
from langchain_core.tools import StructuredTool
from pydantic import BaseModel


class BrowserTask(BaseModel):
    task: str  # The specific task for the browser agent to perform

def execute_browser_task(task: str) -> Dict:
    """Execute a browser-based task using the Agent.

    Args:
        task (str): The specific browser task to execute.

    Returns:
        Dict: The result of the browser task execution.
    """
    async def main():
        agent = Agent(
            task=task,
            llm=ChatOpenAI(model="gpt-4o-mini"),
        )
        result = await agent.run()
        return result

    return asyncio.run(main())

def get_browser_task_tool():
    return StructuredTool.from_function(
        name="browser_task",
        func=execute_browser_task,
        description=(
            " - Only use for complex browser tasks; A more powerful tool executes more complex browser-based task such as navigating to a website, performing a search, and retrieving information.\n"
            "browser_task(task: str) -> dict:\n"
            " - Returns the result as a dictionary.\n"
        ),
        input_schema=BrowserTask,
    )

def test_browser_task_tool():
    test_task = (
        "Go to Reddit, search for 'browser-use' in the search bar, "
        "click on the first post and return the first comment."
    )

    try:
        # Using the tool to execute the browser task
        task_result = execute_browser_task(test_task)

        # Log the result of the task
        print(f"Task result: {task_result}")

    except Exception as e:
        # Log any error that occurs during task execution
        print(f"Error during browser task execution: {e}")

# Uncomment to test the tool
# test_browser_task_tool()