import os

from langchain_core.tools import StructuredTool
from pydantic import BaseModel


class LLMProviderChangeRequest(BaseModel):
    provider: str  # The new LLM provider (e.g., "deepseek", "openai")


def change_llm_provider(provider: str) -> str:
    """Change the LLM provider by updating the environment variable.

    Args:
        provider (str): The new LLM provider (e.g., "deepseek", "openai").

    Returns:
        str: A confirmation message indicating the change.
    """
    # Validate the provider
    valid_providers = ["deepseek", "openai", "huggingface"]
    if provider not in valid_providers:
        return f"Invalid provider. Valid options are: {', '.join(valid_providers)}"

    # Update the environment variable
    os.environ["LLM_PROVIDER"] = provider

    # Return a confirmation message
    return f"LLM provider changed to: {provider}"


def get_llm_provider_tool():
    return StructuredTool.from_function(
        name="change_llm_provider",
        func=change_llm_provider,
        description=(
            "Change the LLM provider by updating the environment variable.\n"
            "change_llm_provider(provider: str) -> str:\n"
            " - Valid providers: 'deepseek', 'openai', 'huggingface'.\n"
            " - Returns a confirmation message.\n"
        ),
        input_schema=LLMProviderChangeRequest,
    )
