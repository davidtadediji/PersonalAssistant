from pydantic import BaseModel
from typing import List, Dict, ClassVar
from langchain_core.tools import StructuredTool

class ToolRegistry:
    def __init__(self):
        self.tools = []

    def add(self, tool):
        """
        Adds a tool to the registry.
        """
        self.tools.append(tool)

    def get_all_tools(self):
        """
        Returns all tools in the registry.
        """
        return self.tools

    def get_tool_by_name(self, name):
        """
        Returns a tool by its name from the registry.
        """
        for tool in self.tools:
            if tool.__class__.__name__ == name:
                return tool
        return None


# Create the ToolRegistry instance
tools_registry = ToolRegistry()

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

    @classmethod
    def get_all_tool_summaries(cls) -> Dict[str, List[Dict[str, str]]]:
        """
        Return a dictionary where keys are category names and values are lists of tool summaries
        (name and short description) for all categories.
        """
        return {
            category.name: category.get_tool_summaries()
            for category in cls.all_categories
        }

    @classmethod
    def filter_tools_by_category(cls, selected_categories: List[str]) -> List[StructuredTool]:
        """
        Filter tools based on selected categories and return the full StructuredTool instances.

        Args:
            selected_categories (List[str]): A list of category names to filter by.

        Returns:
            List[StructuredTool]: A list of StructuredTool instances that belong to the selected categories.
        """
        if not selected_categories:
            # If no categories are selected, return all tools
            return [tool for category in cls.all_categories for tool in category.tools]

        filtered_tools = []
        for category in cls.all_categories:
            if category.name in selected_categories:
                filtered_tools.extend(category.tools)

        return filtered_tools

