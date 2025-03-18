import os

import requests
from dotenv import load_dotenv
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from src.logger import configured_logger  # Assuming the logger is imported here

# Load environment variables
load_dotenv()


class WolframAlphaQuery(BaseModel):
    """The input for Wolfram Alpha query."""

    query: str = Field(..., description="The query to send to Wolfram Alpha.")
    max_chars: int = Field(
        6800, description="The maximum number of characters in the response."
    )


def wolfram_alpha_computing(query: str, max_chars: int = 800) -> str:
    """
    Query Wolfram Alpha API with better handling of partial inputs.

    Args:
        query (str): The query for Wolfram Alpha.
        max_chars (int): The maximum number of characters in the response (default is 6800).

    Returns:
        str: The raw response from the Wolfram Alpha API or an error message with guidance.
    """
    try:
        # Log the incoming query
        configured_logger.info(f"Query received: {query}")

        # Retrieve the app_id from the environment variable
        app_id = os.getenv("WOLFRAM_ALPHA_APP_ID")  # Default to "DEMO" if not set

        if not query:
            error_message = "Error: No query provided. Please provide a valid query to proceed."
            configured_logger.error(error_message)
            return error_message

        base_url = "http://api.wolframalpha.com/v1/result"  # Short Answer API URL
        params = {"input": query, "appid": app_id, "maxchars": max_chars}

        # Log the API request parameters
        configured_logger.info(f"Sending request to Wolfram Alpha with params: {params}")

        response = requests.get(base_url, params=params)

        response.raise_for_status()  # Raise HTTPError for bad responses

        if response.status_code == 200:
            configured_logger.info("Wolfram Alpha response successfully received.")
            return response.text
        else:
            error_message = f"Error: {response.status_code} - {response.text}"
            configured_logger.error(error_message)
            raise Exception(error_message)

    except requests.exceptions.RequestException as e:
        error_message = f"Error occurred during Wolfram Alpha API call -> {e}"
        configured_logger.error(error_message)
        return error_message


# Define the structured tool
def get_wolfram_tool():
    return StructuredTool.from_function(
        name="wolfram_alpha",
        func=wolfram_alpha_computing,
        description=(
            'Sends a query to the Wolfram Alpha API and returns the response.\n'
            'Wolfram Alpha handles natural language queries across various domains, including math, science, and art.\n'
            'Supports calculations, conversions, formula solving, and more. Simplify inputs into keywords where possible.\n'
            'Queries must be in English. Translate if necessary but reply in the original language.\n'
            'Use Markdown for math formatting:\n'
            '    - Standalone math: `$$[expression]$$`\n'
            '    - Inline math: `\\([expression]\\)`\n'
            'Follow these conventions:\n'
            '    - Use `6 * 10 ^ 14` instead of `6e14`.\n'
            '    - Prefer single-letter variable names and named constants (e.g., \'speed of light\').\n'
            '    - Separate compound units with spaces (e.g., \'Ω m\').\n'
            'Solve equations without units for clarity; include real units only where necessary.\n'
            'Handle irrelevant results by re-sending queries with assumptions or asking for user input if needed.\n'
            'Parameters:\n'
            '    query: The single line input string to search.\n'
            '    max_chars: Specifies the maximum character limit for the response.\n'
            'Returns:\n'
            '    A text response based on the query,'
        ),
        input_schema=WolframAlphaQuery,
    )
