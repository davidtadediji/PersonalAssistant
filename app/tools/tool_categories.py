from typing import List, ClassVar, Sequence
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, model_validator
from langchain_core.tools import BaseTool

from app.tools.tool_list import science_and_computation, reverse_geocode, geocode_location, current_location, \
    store_user_personal_info, retrieve_user_personal_info, extract_raw_content_from_url, weather_information, tools


# Assuming Tool and StructuredTool are properly defined in the appropriate modules
class Tool(BaseModel):
    """
    Represents a tool with a name and a short description.
    """
    name: str
    description: str


class ToolCategory(BaseModel):
    """
    Represents a category of tools with a description, category name, and list of tools.
    """
    name: str
    description: str
    tools: List[Tool]

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

    def add_tool(self, tool: Tool):
        """
        Add a tool to the category.

        :param tool: A Tool instance to add to the category.
        """
        self.tools.append(tool)

    def list_tools(self):
        """
        List all tools in the category.

        :return: A list of tools with their names and descriptions.
        """
        return self.tools

    @model_validator(mode='before')
    def parse_tools(cls, values):
        """
        Ensure that tools are instances of the Tool model or StructuredTool.
        If a StructuredTool is provided, extract the name and description and convert to Tool.
        """
        tools = values.get('tools', [])

        # Check if tools is a list of StructuredTools and convert them into Tool instances
        if tools and isinstance(tools, list):
            values['tools'] = [
                Tool(name=tool.name, description=tool.description.split("\n")[0]) if isinstance(tool, StructuredTool)
                else tool
                for tool in tools
            ]

        # Ensure all tools are Tool instances (for type safety)
        for idx, tool in enumerate(values['tools']):
            if not isinstance(tool, Tool):
                raise ValueError(f"Tool at index {idx} is not a valid Tool instance.")

        return values


# Define categories
def create_tool_category(name: str, description: str, tools: List):
    for tool in tools:
        if not isinstance(tool, (Tool, StructuredTool)):
            raise ValueError(f"Invalid tool: {type(tool)}")
    ToolCategory(name=name, description=description, tools=tools)


create_tool_category("Computation", "Tools for performing computations and scientific tasks.",
                     [science_and_computation])

# Create more tool categories
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

def filter_tools_by_category(selected_categories: List[str]) -> List[BaseTool]:
    """
    Filter tools based on selected categories.
    """
    if not selected_categories:
        return tools  # Return all tools if no categories are selected
    tool_categories.tools for tool_category_name in selected_categories
    return [tool for tool in tools if getattr(tool, "category", None) in selected_categories]

# Print tool categories
for c in tool_categories:
    print(c.model_dump(mode='json'))
