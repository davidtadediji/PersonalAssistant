import getpass
import os
from typing import Sequence

from dotenv import load_dotenv
from langchain import hub
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
    FunctionMessage,
    SystemMessage,
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableBranch
from langchain_core.tools import BaseTool
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

from app.llm_compiler.output_parser import LLMCompilerPlanParser
from app.tools.current_location_tool import get_current_location_tool
from app.tools.geocode_tool import get_geocode_location_tool
from app.tools.image_url_interpreter_tool import get_image_url_interpreter_tool
from app.tools.personal_information_tool import (
    get_store_user_personal_info_tool,
    get_retrieve_user_personal_info_tool,
)
from app.tools.reverse_geocode_tool import get_reverse_geocode_tool
from app.tools.tavily_extract_tool import get_tavily_extract_tool
from app.tools.weather_forecast_tool import (
    get_weather_forecast_tool,
)
from app.tools.wolfram_tool import get_wolfram_tool

load_dotenv()

prompt = hub.pull("wfh/llm-compiler")
print(prompt.pretty_print())


def _get_pass(var: str):
    if var not in os.environ:
        os.environ[var] = getpass.getpass(f"{var}: ")


_get_pass("OPENAI_API_KEY")


# TODO: convert to planner agent; make planner use tool functions instead of BaseTool
def create_planner(
        llm: BaseChatModel, tools: Sequence[BaseTool], base_prompt: ChatPromptTemplate
):
    tool_descriptions = "\n".join(
        f"{i + 1}. {tool.description}\n"
        for i, tool in enumerate(
            tools
        )  # +1 to offset the 0 starting index, we want it count normally from 1.
    )
    planner_prompt = base_prompt.partial(
        replan="",
        num_tools=len(tools)
                  + 1,  # Add one because we're adding the join() tool at the end.
        tool_descriptions=tool_descriptions,
    )
    re_planner_prompt = base_prompt.partial(
        replan=' - You are given "Previous Plan" which is the plan that the previous agent created along with the execution results '
               "(given as Observation) of each plan and a general thought (given as Thought) about the executed results."
               'You MUST use these information to create the next plan under "Current Plan".\n'
               ' - When starting the Current Plan, you should start with "Thought" that outlines the strategy for the next plan.\n'
               " - In the Current Plan, you should NEVER repeat the actions that are already executed in the Previous Plan.\n"
               " - You must continue the task index from the end of the previous one. Do not repeat task indices.",
        num_tools=len(tools) + 1,
        tool_descriptions=tool_descriptions,
    )

    def should_re_plan(state: list):
        # Context is passed as a system message
        return isinstance(state[-1], SystemMessage)

    def wrap_messages(state: list):
        return {"messages": state}

    def wrap_and_get_last_index(state: list):
        next_task = 0
        for message in state[::-1]:
            if isinstance(message, FunctionMessage):
                next_task = message.additional_kwargs["idx"] + 1
                break
        state[-1].content = state[-1].content + f" - Begin counting at : {next_task}"
        return {"messages": state}

    return (
            RunnableBranch(
                (should_re_plan, wrap_and_get_last_index | re_planner_prompt),
                wrap_messages | planner_prompt,
            )
            | llm
            | LLMCompilerPlanParser(tools=tools)
    )


from langchain_community.tools.tavily_search import TavilySearchResults

from app.tools.math_tools import get_math_tool

_get_pass("TAVILY_API_KEY")

calculate = get_math_tool(ChatOpenAI(model=os.getenv("EXECUTION_MODEL")))
# calculate = get_math_tool(ChatGroq(model="mixtral-8x7b-32768"))
science_and_computation = get_wolfram_tool()
geocode_location = get_geocode_location_tool()
reverse_geocode = get_reverse_geocode_tool()
current_location = get_current_location_tool()
extract_raw_content_from_url = get_tavily_extract_tool()
weather_information = get_weather_forecast_tool()
image_url_interpreter = get_image_url_interpreter_tool()
store_user_personal_info = get_store_user_personal_info_tool()
retrieve_user_personal_info = get_retrieve_user_personal_info_tool()

search = TavilySearchResults(
    max_results=1,
    description='tavily_search_results_json(query="the search query") - a search engine. Where appropriate, it could be defaulted to after several attempts at using a more specific tool to accomplish a task but fails.',
)

tools = [
    search,
    science_and_computation,
    geocode_location,
    weather_information,
    reverse_geocode,
    current_location,
    extract_raw_content_from_url,
    image_url_interpreter,
    store_user_personal_info,
    retrieve_user_personal_info,
]
planner = create_planner(
    # ChatOpenAI(model=os.getenv("PLANNING_MODEL")),
    ChatGroq(model="llama-3.3-70b-specdec"),
    tools
    ,
    prompt
)
