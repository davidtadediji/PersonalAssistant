from typing import List, ClassVar, Dict
from langchain_core.tools import StructuredTool
from pydantic import BaseModel

from app.tools.tool_registry import science_and_computation, reverse_geocode, geocode_location, current_location, \
    store_user_personal_info, retrieve_user_personal_info, extract_raw_content_from_url, weather_information, tools_registry


class ToolCategory(BaseModel):
    """
    Represents a category of tools with a description, category name, and list of StructuredTool instances.
    """
    name: str
    description: str
    tools: List[StructuredTool]  # Directly store StructuredTool instances

    all_categories: ClassVar[List["ToolCategory"]] = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        ToolCategory._add_category(self)

    @classmethod
    def _add_category(cls, category: "ToolCategory"):
        """
        Class method to add the category to the all_categories list.
        """
        if not hasattr(cls, 'all_categories'):
            cls.all_categories = []  # Ensure it's initialized before use
        cls.all_categories.append(category)

    def get_tool_summaries(self) -> List[Dict[str, str]]:
        """
        Return a list of tool summaries (name and short description) for this category.
        """
        return [{"name": tool.name, "description": tool.description.split("\n")[0]} for tool in self.tools]


# Define categories
def create_tool_category(name: str, description: str, tools: List[StructuredTool]):
    """
    Create a tool category and add it to the global list of categories.
    """
    for tool in tools:
        if not isinstance(tool, StructuredTool):
            raise ValueError(f"Invalid tool: {type(tool)}. Expected StructuredTool.")
    ToolCategory(name=name, description=description, tools=tools)


# Create tool categories
create_tool_category(
    "Computation",
    "Tools for performing computations and scientific tasks.",
    [science_and_computation]
)

create_tool_category(
    "Location Information",
    "Tools for geolocation, mapping, and location-based tasks.",
    [geocode_location, reverse_geocode, current_location]
)

create_tool_category(
    "Weather Information",
    "Tools for weather forecast and information.",
    [weather_information]
)

create_tool_category(
    "Content Extraction",
    "Tools for extracting content from various sources.",
    [extract_raw_content_from_url]
)

create_tool_category(
    "User Personal Info Management",
    "Tools for storing and retrieving user personal information.",
    [store_user_personal_info, retrieve_user_personal_info]
)

tool_categories = ToolCategory.all_categories


def get_all_tool_summaries() -> Dict[str, List[Dict[str, str]]]:
    """
    Return a dictionary where keys are category names and values are lists of tool summaries
    (name and short description) for all categories.
    """
    return {
        category.name: category.get_tool_summaries()
        for category in tool_categories
    }


def filter_tools_by_category(selected_categories: List[str]) -> List[StructuredTool]:
    """
    Filter tools based on selected categories and return the full StructuredTool instances.

    Args:
        selected_categories (List[str]): A list of category names to filter by.

    Returns:
        List[StructuredTool]: A list of StructuredTool instances that belong to the selected categories.
    """
    if not selected_categories:
        # If no categories are selected, return all tools
        return tools_registry

    filtered_tools = []
    for category in tool_categories:
        if category.name in selected_categories:
            filtered_tools.extend(category.tools)

    return filtered_tools

# print(filter_tools_by_category(["User Personal Info Management"]))