import os
from typing import Dict

from dotenv import load_dotenv
from langchain_core.tools import StructuredTool
from openai import OpenAI
from pydantic import BaseModel, Field

from src.logger import configured_logger

load_dotenv()
# Initialize the OpenAI client
client = OpenAI()


class ImageUrlInterpreterInput(BaseModel):
    url: str = Field(..., description="The URL of the image to be interpreted.")


def image_url_interpreter(url: str) -> Dict:
    """Interpret the content of an image URL using OpenAI API.

    Args:
        url (str): The URL of the image to be interpreted.

    Returns:
        dict: The result from the OpenAI API containing the interpretation of the image.
    """
    try:
        # Log the incoming request to interpret the image
        configured_logger.info(f"Request received to interpret image from URL: {url}")

        # Send the image URL to the OpenAI API for interpretation
        response = client.chat.completions.create(
            model=os.getenv("EXECUTION_MODEL"),
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "What's in this image?"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": url,
                                "detail": "high",  # Set the image detail level, can be "high", "medium", "low"
                            },
                        },
                    ],
                }
            ],
            max_tokens=300,
        )

        # Log successful interpretation
        configured_logger.info(f"Successfully interpreted image from URL: {url}")

        # Extract the content from the response and return it
        return {
            "success": True,
            "image_url": url,
            "interpretation": response.choices[0].message.content,
        }

    except Exception as e:
        # Log the error that occurred
        configured_logger.error(f"Error occurred while interpreting image from URL: {url}. Error: {str(e)}")
        return {"error": f"An error occurred: {str(e)}"}


def get_image_url_interpreter_tool():
    return StructuredTool.from_function(
        name="image_url_interpreter",
        func=image_url_interpreter,
        description=(
            "image_url_interpreter(url: str) -> dict:\n"
            " - Interprets the content of an image from a URL using the OpenAI API.\n"
            " - Returns a dictionary containing the image URL and the interpretation of its content.\n"
        ),
        input_schema=ImageUrlInterpreterInput,  # Using the correct input schema model here
    )
