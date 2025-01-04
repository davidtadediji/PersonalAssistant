import os
from datetime import datetime
from typing import List, Dict
import requests
from dotenv import load_dotenv
from langchain_core.tools import StructuredTool
from pydantic import BaseModel

from app.logger import configured_logger

load_dotenv()


class TavilyExtractQuery(BaseModel):
    urls: List[str]  # A list of URLs to extract content from


def extract_raw_content_from_url(urls: List[str]) -> Dict:
    """Retrieve raw web content from specified URLs using the Tavily API.

    Args:
        urls (List[str]): The list of URLs to extract content from.

    Returns:
        Dict: A dictionary containing the extraction results, including raw content and any errors.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    base_url = os.getenv("TAVILY_API_URL")
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    try:
        # Log the incoming URLs
        configured_logger.info(f"Extracting content from URLs: {urls}")

        payload = {"urls": urls}

        # Log the API request being sent
        configured_logger.info(f"Sending extraction request to Tavily API with payload: {payload}")

        # Synchronous request using requests
        response = requests.post(f"{base_url}/extract", headers=headers, json=payload)

        if response.status_code == 200:
            results = response.json()

            # Log the successful response
            configured_logger.info("Tavily API response received successfully.")

            formatted_results = {
                "timestamp": datetime.now().isoformat(),
                "success": True,
                "results": [],
                "failed_results": [],
                "response_time": results.get("response_time", "N/A"),
            }

            if "results" in results:
                formatted_results["results"] = [
                    {"url": r["url"], "raw_content": r["raw_content"]}
                    for r in results["results"]
                ]

            if "failed_results" in results:
                formatted_results["failed_results"] = [
                    {"url": r["url"], "error": r["error"]} for r in results["failed_results"]
                ]

            return formatted_results
        else:
            error_msg = response.text
            # Log the error from the response
            configured_logger.error(f"Extraction failed with error: {error_msg}")
            raise Exception(f"Extraction failed -> {error_msg}") from Exception(error_msg)

    except Exception as e:
        # Log the exception that occurred
        configured_logger.error(f"Tavily extract failed -> {e}")
        raise Exception(f"Tavily extract failed -> {e}") from e


def get_tavily_extract_tool():
    return StructuredTool.from_function(
        name="tavily_extract",
        func=extract_raw_content_from_url,
        description=(
            "tavily_extract(urls: List[str]) -> dict:\n"
            " - Retrieve raw web content from specified URLs using the Tavily API.\n"
            " - Returns a dictionary with the extraction results, including raw content and any errors.\n"
        ),
        input_schema=TavilyExtractQuery,
    )


def test_tavily_extract_tool():
    # Define some test URLs to pass to the extraction function
    test_urls = [
        "https://www.wolframalpha.com/examples/mathematics/elementary-math",
        "https://example.org",
    ]

    # Call the extract function
    try:
        # Using the tool defined earlier to extract raw content from URLs
        extract_result = extract_raw_content_from_url(test_urls)

        # Log the result of the extraction
        configured_logger.info(f"Extraction result: {extract_result}")

    except Exception as e:
        # Log any error that occurs during the extraction process
        configured_logger.error(f"Error during extraction: {e}")


test_tavily_extract_tool()
