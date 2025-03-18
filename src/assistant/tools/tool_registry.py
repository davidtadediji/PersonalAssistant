import os

from langchain_community.tools.tavily_search import TavilySearchResults

from src.assistant.planning.llm_initializer import execution_llm
from src.assistant.tools.computation.math import get_math_tool
from src.assistant.tools.computation.wolfram import get_wolfram_tool
from src.assistant.tools.content_extraction.image_url_interpreter import get_image_url_interpreter_tool
from src.assistant.tools.location_information.current_location import get_current_location_tool
from src.assistant.tools.location_information.geocode import get_geocode_location_tool
from src.assistant.tools.location_information.reverse_geocode import get_reverse_geocode_tool
from src.assistant.tools.manage_personal_info import (
    get_store_user_personal_info_tool,
    get_retrieve_user_personal_info_tool,
)
from src.assistant.tools.weather_forecast import (
    get_weather_forecast_tool,
)
from src.assistant.tools.web_browsing.browser_use import get_browser_task_tool
from src.assistant.tools.web_browsing.tavily_extract import get_tavily_extract_tool

os.getenv("TAVILY_API_KEY")

calculate = get_math_tool(execution_llm)
# calculate = get_math_tool(ChatGroq(model="mixtral-8x7b-32768"))
science_and_computation = get_wolfram_tool()
geocode_location = get_geocode_location_tool()
reverse_geocode = get_reverse_geocode_tool()
current_location = get_current_location_tool()
extract_raw_content_from_url = get_tavily_extract_tool()
weather_information = get_weather_forecast_tool()
image_url_interpreter = get_image_url_interpreter_tool()
store_user_personal_info = get_store_user_personal_info_tool()
retrieve_user_personal_info = get_retrieve_user_personal_info_tool()
browser_use = get_browser_task_tool()
search_engine = TavilySearchResults(
    max_results=1,
    description='tavily_search_results_json(query="the search query") - a search engine. Where appropriate, it could be defaulted to after several attempts at using a more specific tool to accomplish a task but fails.',
)

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

# Add tools to the registry
tools_registry.add(search_engine)
tools_registry.add(browser_use)
tools_registry.add(geocode_location)
tools_registry.add(weather_information)
tools_registry.add(reverse_geocode)
tools_registry.add(current_location)
tools_registry.add(extract_raw_content_from_url)
tools_registry.add(image_url_interpreter)
tools_registry.add(store_user_personal_info)
tools_registry.add(retrieve_user_personal_info)

# Example: Getting all tools
all_tools = tools_registry.get_all_tools()
for tool in all_tools:
    print(tool)

# Example: Get a specific tool by name
specific_tool = tools_registry.get_tool_by_name('TavilySearchResults')
print(specific_tool)
