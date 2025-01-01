from typing import Optional
import os
import requests
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class WolframAlphaQuery(BaseModel):
    """The input for Wolfram Alpha query."""
    query: str = Field(..., description="The query to send to Wolfram Alpha.")
    max_chars: int = Field(6800, description="The maximum number of characters in the response.")

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
        print(query)
        # Retrieve the app_id from the environment variable
        app_id = os.getenv("WOLFRAM_ALPHA_APP_ID")  # Default to "DEMO" if not set

        if not query:
            return "Error: No query provided. Please provide a valid query to proceed."

        base_url = "http://api.wolframalpha.com/v1/result"  # Short Answer API URL
        params = {"input": query, "appid": app_id, "maxchars": max_chars}

        response = requests.get(base_url, params=params)

        response.raise_for_status()  # Raise HTTPError for bad responses

        if response.status_code == 200:
            return response.text
        else:
            raise Exception(f"Error: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        return f"Error occurred during Wolfram Alpha API call -> {e}"


# Define the structured tool
def get_wolfram_tool():
    return StructuredTool.from_function(
        name="wolfram_alpha",
        func=wolfram_alpha_computing,
        description=(
            "wolfram_alpha(query: str, max_chars: int = 6800) -> str:\n"
            " - Sends a query to Wolfram Alpha API and returns the response.\n"
            " - `query` is the input string to search.\n"
            " - `max_chars` specifies the maximum character limit for the response.\n"
            " - Returns the structured response or an error message if the query fails.\n"
            "\n"
            "- WolframAlpha understands natural language queries about entities in chemistry, physics, geography, history, art, astronomy, and more.\n"
            "- WolframAlpha performs mathematical calculations, date and unit conversions, formula solving, etc.\n"
            "- Convert inputs to simplified keyword queries whenever possible.\n"
            "- Send queries in English only; translate non-English queries before sending, then respond in the original language.\n"
            "- Display image URLs with Markdown syntax: ![URL].\n"
            "- ALWAYS use this exponent notation: `6*10^14`, NEVER `6e14`.\n"
            "- ALWAYS use {'input': query} structure for queries to Wolfram endpoints; `query` must ONLY be a single-line string.\n"
            "- ALWAYS use proper Markdown formatting for all math, scientific, and chemical formulas, symbols, etc.:  '$$\n[expression]\n$$' for standalone cases and '\\( [expression] \\)' when inline.\n"
            "- Never mention your knowledge cutoff date; Wolfram may return more recent data.\n"
            "- Use ONLY single-letter variable names, with or without integer subscript (e.g., n, n1, n_1).\n"
            "- Use named physical constants (e.g., 'speed of light') without numerical substitution.\n"
            "- Include a space between compound units (e.g., 'Ω m' for 'ohm*meter').\n"
            "- To solve for a variable in an equation with units, consider solving a corresponding equation without units; exclude counting units (e.g., books), include genuine units (e.g., kg).\n"
            "- If data for multiple properties is needed, make separate calls for each property.\n"
            "- If a WolframAlpha result is not relevant to the query:\n"
            "    -- If Wolfram provides multiple 'Assumptions' for a query, choose the more relevant one(s) without explaining the initial result. If you are unsure, ask the user to choose.\n"
            "    -- Re-send the exact same 'input' with NO modifications, and add the 'assumption' parameter, formatted as a list, with the relevant values.\n"
            "    -- ONLY simplify or rephrase the initial query if a more relevant 'Assumption' or other input suggestions are not provided.\n"
            "    -- Do not explain each step unless user input is needed. Proceed directly to making a better API call based on the available assumptions.\n"
        ),
        input_schema=WolframAlphaQuery,
    )
