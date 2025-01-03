from pydantic import BaseModel, Field
from typing import Dict
import os
from dotenv import load_dotenv
from langchain_core.tools import StructuredTool
from openai import OpenAI

from app.llm_compiler.llm_initializer import execution_llm

load_dotenv()
client = OpenAI()

class GeneralKnowledgeInput(BaseModel):
    question: str = Field(..., description="The question to ask the model.")


def general_knowledge_up_to_2022(question: str) -> Dict:
    """Send a question to the LLM with knowledge cutoff up to 2022 and return the response.

    Args:
        question (str): The question to ask the LLM.

    Returns:
        dict: The result from the LLM containing the response based on knowledge up to 2022.
    """
    try:
        messages = [
            (
                "system",
                "You are a helpful assistant",
            ),
            ("human", question),
        ]
        # Pass the message
        response = execution_llm.invoke(
            input=messages,
        )
        # Extract the content from the response and return it
        return {
            "success": True,
            "input_message": question,
            "response": response.choices[0].message.content,
        }


    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}


def get_general_knowledge_tool():
    return StructuredTool.from_function(
        name="general_knowledge_up_to_2022",
        func=general_knowledge_up_to_2022,
        description=(
            "general_knowledge_up_to_2022(question: str) -> dict:\n"
            " - Provides answers to general knowledge questions based on information available up to the year 2022.\n"
            " - Returns a dictionary containing the input question and the LLM's response based on the knowledge up to 2022.\n"
        ),
        input_schema=GeneralKnowledgeInput,  # Using the correct input schema model here
    )
