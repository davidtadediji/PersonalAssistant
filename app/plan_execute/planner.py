import os
from typing import List
from dotenv import load_dotenv
from langchain.chains.structured_output import create_openai_fn_runnable
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import Field, BaseModel
from app.prompt import planner_prompt, re_planner_prompt

load_dotenv()

class Plan(BaseModel):
    """Plan to follow in future"""
    steps: List[str] = Field(
        description="different steps to follow, should be in sorted order"
    )

class Response(BaseModel):
    """Response to user."""
    response: str

llm = ChatOpenAI(model=os.getenv("PLANNING_MODEL"))
structured_llm = llm.with_structured_output(Plan)

planner_prompt = ChatPromptTemplate.from_template(planner_prompt)
planner = planner_prompt | structured_llm

# response = planner.invoke(
#     {"objective": "What is the hometown of the current Australia open winner?"}
# )
#
# print(response)

re_planner_prompt = ChatPromptTemplate.from_template(re_planner_prompt)
re_planner = create_openai_fn_runnable([Plan, Response], llm, re_planner_prompt)