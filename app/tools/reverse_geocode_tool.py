import os
from typing import Optional
import requests
from dotenv import load_dotenv
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from app.logger import configured_logger

load_dotenv()


class ReverseGeocodeQuery(BaseModel):
    lat: float = Field(..., description="The latitude coordinate.")
    lon: float = Field(..., description="The longitude coordinate.")
    limit: Optional[int] = Field(
        5, description="The number of location names to return (default is 5)."
    )


def reverse_geocode(lat: float, lon: float, limit: int = 5) -> dict:
    api_key = os.getenv("OPENWEATHER_API_KEY")
    api_url = os.getenv("OPENWEATHER_REVERSE_GEOCODE_URL")

    url = f"{api_url}?lat={lat}&lon={lon}&limit={limit}&appid={api_key}"
    configured_logger.info(f"Making reverse geocoding request to URL: {url}")

    try:
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            if not data:
                configured_logger.warning(f"No matching locations found for coordinates ({lat}, {lon}).")
                return {"error": "No matching locations found."}
            configured_logger.info(f"Reverse geocoding successful for coordinates ({lat}, {lon}).")
            return data
        else:
            configured_logger.error(f"Request failed with status code {response.status_code}.")
            return {"error": f"Request failed with status code {response.status_code}."}
    except Exception as e:
        configured_logger.error(f"Error during reverse geocoding request: {e}")
        return {"error": f"Error: {e}"}


def get_reverse_geocode_tool():
    return StructuredTool.from_function(
        name="reverse_geocode",
        func=reverse_geocode,
        description=(
            "reverse_geocode(lat: float, lon: float, limit: int) -> dict:\n"
            " - Performs reverse geocoding to get location names from geographical coordinates.\n"
            " - Returns a list of matching locations or an error message if no results are found.\n"
        ),
        input_schema=ReverseGeocodeQuery,
    )
