import os
from typing import Optional, List
import requests
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from app.logger import configured_logger


class PerplexitySearchQuery(BaseModel):
    query: str = Field(..., description="The user's query.")
    model: str = Field(
        default="llama-3.1-sonar-small-128k-online",
        description="The language model to use.",
    )
    max_tokens: Optional[int] = Field(
        None, description="Maximum number of tokens in the response."
    )
    temperature: float = Field(
        default=0.2, description="Sampling temperature for response generation."
    )
    top_p: float = Field(default=0.9, description="Nucleus sampling parameter.")
    search_domain_filter: Optional[List[str]] = Field(
        None, description="Domains to restrict search results to."
    )
    return_images: bool = Field(
        default=False, description="Whether to include images in the response."
    )
    return_related_questions: bool = Field(
        default=False, description="Whether to return related questions."
    )
    search_recency_filter: str = Field(
        default="month", description="Recency filter for the search (e.g., 'month')."
    )
    top_k: int = Field(default=0, description="Number of top results to return.")
    presence_penalty: float = Field(
        default=0.0, description="Presence penalty for token generation."
    )
    frequency_penalty: float = Field(
        default=1.0, description="Frequency penalty for token generation."
    )


def perplexity_search(
        query,
        model="llama-3.1-sonar-small-128k-online",
        max_tokens=None,
        temperature=0.2,
        top_p=0.9,
        search_domain_filter=None,
        return_images=False,
        return_related_questions=False,
        search_recency_filter="month",
        top_k=0,
        presence_penalty=0,
        frequency_penalty=1,
):
    """
    Queries the Perplexity API with the provided parameters.

    Args:
        query (str): The user's query.
        model (str): The language model to use.
        max_tokens (int or None): Maximum number of tokens in the response.
        temperature (float): Sampling temperature for response generation.
        top_p (float): Nucleus sampling parameter.
        search_domain_filter (list or None): Domains to restrict search results to.
        return_images (bool): Whether to include images in the response.
        return_related_questions (bool): Whether to return related questions.
        search_recency_filter (str): Recency filter for the search (e.g., "month").
        top_k (int): Number of top results to return.
        presence_penalty (float): Presence penalty for token generation.
        frequency_penalty (float): Frequency penalty for token generation.

    Returns:
        dict: The API response as a JSON object.
    """
    if not query:
        configured_logger.error("Query cannot be empty.")
        return {"error": "Query cannot be empty."}

    token = os.getenv("PERPLEXITY_TOKEN")

    if not token:
        configured_logger.error("API token is required.")
        return {"error": "API token is required."}

    url = os.getenv("PERPLEXITY_API_URL")

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Be precise and concise."},
            {"role": "user", "content": query},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "search_domain_filter": search_domain_filter or ["perplexity.ai"],
        "return_images": return_images,
        "return_related_questions": return_related_questions,
        "search_recency_filter": search_recency_filter,
        "top_k": top_k,
        "presence_penalty": presence_penalty,
        "frequency_penalty": frequency_penalty,
    }

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    try:
        configured_logger.info(f"Querying Perplexity API with query: {query}")
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        configured_logger.info(f"API response received successfully for query: {query}")
        return response.json()
    except requests.RequestException as e:
        configured_logger.error(f"Error occurred while querying Perplexity API: {str(e)}")
        return {"error": str(e)}


def perplexity_search_tool() -> StructuredTool:
    return StructuredTool.from_function(
        name="perplexity_search",
        func=perplexity_search,
        description=(
            "Queries the Perplexity API with the provided parameters.\n"
            " - query: The user's search query.\n"
            " - model: The language model to use (default: 'llama-3.1-sonar-small-128k-online').\n"
            " - max_tokens: Maximum number of tokens in the response (optional).\n"
            " - temperature: Sampling temperature for response generation (default: 0.2).\n"
            " - top_p: Nucleus sampling parameter (default: 0.9).\n"
            " - search_domain_filter: Domains to restrict search results to (default: ['perplexity.ai']).\n"
            " - return_images: Whether to include images in the response (default: False).\n"
            " - return_related_questions: Whether to return related questions (default: False).\n"
            " - search_recency_filter: Recency filter for the search (default: 'month').\n"
            " - top_k: Number of top results to return (default: 0).\n"
            " - presence_penalty: Presence penalty for token generation (default: 0.0).\n"
            " - frequency_penalty: Frequency penalty for token generation (default: 1.0)."
        ),
        input_schema=PerplexitySearchQuery,
    )
