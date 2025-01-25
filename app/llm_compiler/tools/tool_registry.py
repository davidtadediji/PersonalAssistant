import os

from langchain_community.tools.tavily_search import TavilySearchResults

from app.llm_compiler.llm_initializer import execution_llm
from app.llm_compiler.tools.computation.math import get_math_tool
from app.llm_compiler.tools.computation.wolfram import get_wolfram_tool
from app.llm_compiler.tools.content_extraction.image_url_interpreter import get_image_url_interpreter_tool
from app.llm_compiler.tools.location_information.current_location import get_current_location_tool
from app.llm_compiler.tools.location_information.geocode import get_geocode_location_tool
from app.llm_compiler.tools.location_information.reverse_geocode import get_reverse_geocode_tool
from app.llm_compiler.tools.manage_personal_info import (
    get_store_user_personal_info_tool,
    get_retrieve_user_personal_info_tool,
)
from app.llm_compiler.tools.weather_forecast import (
    get_weather_forecast_tool,
)
from app.llm_compiler.tools.web_browsing.browser_use import get_browser_task_tool
from app.llm_compiler.tools.web_browsing.tavily_extract import get_tavily_extract_tool

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

tools_registry = [
    search_engine,
    browser_use,
    geocode_location,
    weather_information,
    reverse_geocode,
    current_location,
    extract_raw_content_from_url,
    image_url_interpreter,
    store_user_personal_info,
    retrieve_user_personal_info,
]
