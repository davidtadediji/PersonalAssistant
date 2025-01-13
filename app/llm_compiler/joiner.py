from typing import Union, List

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage
from pydantic import BaseModel, Field

from app.llm_compiler.prompts import joiner_prompt

load_dotenv()

class FinalResponse(BaseModel):
    """The final response/answer."""

    response: str


class RePlan(BaseModel):
    feedback: str = Field(
        description="Analysis of the previous attempts and recommendations on what needs to be fixed."
    )


class JoinOutputs(BaseModel):
    """Decide whether to re-plan or whether you can return the final response."""

    thought: str = Field(
        description="The chain of thought reasoning for the selected action"
    )
    action: Union[FinalResponse, RePlan]

from app.llm_compiler.llm_initializer import llm

runnable = joiner_prompt | llm.with_structured_output(JoinOutputs)


def _parse_joiner_output(decision: JoinOutputs) -> List[BaseMessage]:
    response = [AIMessage(content=f"Thought: {decision.thought}")]
    if isinstance(decision.action, RePlan):
        return {
            "messages": response
                        + [
                            SystemMessage(
                                content=f"Context from last attempt: {decision.action.feedback}"
                            )
                        ]
        }
    else:
        return {"messages": response + [AIMessage(content=decision.action.response)]}


def select_recent_messages(state) -> dict:
    messages = state["messages"]
    selected = []
    for msg in messages[::-1]:
        selected.append(msg)
        if isinstance(msg, HumanMessage):
            break
    return {"messages": selected[::-1]}


joiner = select_recent_messages | runnable | _parse_joiner_output

# Test
example_question = "What's the temperature in SF raised to the 3rd power?"

# tool_messages = plan_and_schedule.invoke(
#     {"messages": [HumanMessage(content=example_question)]}
# )["messages"]
#
# input_messages = [HumanMessage(content=example_question)] + tool_messages
#
# # print(joiner.invoke({"messages": input_messages}))
