from typing import Dict
from dotenv import load_dotenv
from langchain_core.tools import StructuredTool
from openai import OpenAI
from pydantic import BaseModel, Field
from app.llm_compiler.llm_initializer import chat_llm

# Load environment variables
load_dotenv()
# Initialize the OpenAI client
client = OpenAI()


class DirectResponseInput(BaseModel):
    message: str = Field(
        ..., description="The message to pass directly to the LLM for response."
    )


def direct_response(message: str) -> Dict:
    """Send a direct message to the LLM and return the response.

    Args:
        message (str): The input message to be passed directly to the LLM.

    Returns:
        dict: The result from the LLM containing the response.
    """
    try:
        messages = [
            (
                "system",
                "You are a helpful assistant",
            ),
            ("human", message),
        ]
        # Pass the message
        response = chat_llm.invoke(
            input=messages,
        )
        # Extract the content from the response and return it
        return {
            "response": f"Respond with this: \n {response.content}",
        }

    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}


def get_direct_response_tool():
    return StructuredTool.from_function(
        name="direct_response",
        func=direct_response,
        description=(
            "direct_response(message: str) -> dict:\n"
            " - Evaluates a message that does not require tool call and prescribes exactly what to respond with.\n"
            " - Returns a dictionary containing the input message and the instruction on how to respond.\n"
        ),
        input_schema=DirectResponseInput,  # Using the correct input schema model here
    )
