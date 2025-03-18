import os
from typing import Optional

import requests
from dotenv import load_dotenv
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from src.logger import configured_logger  # Assuming the logger is imported

load_dotenv()


class GeocodeLocationQuery(BaseModel):
    location_name: Optional[str] = Field(
        None, description="The name of the location (e.g., 'London,GB')."
    )
    zip_code: Optional[str] = Field(
        None, description="The zip/postal code (e.g., '90210,US')."
    )
    limit: Optional[int] = Field(
        5, description="The number of locations to return (up to 5)."
    )


def geocode_location(
        location_name: Optional[str] = None, zip_code: Optional[str] = None, limit: int = 5
) -> dict:
    api_key = os.getenv("OPENWEATHER_API_KEY")
    api_url = os.getenv("OPENWEATHER_GEOCODE_URL")

    configured_logger.info("Starting geocode_location function.")

    if location_name:
        url = f"{api_url}/direct?q={location_name}&limit={limit}&appid={api_key}"
        configured_logger.info(f"Geocoding by location name: {location_name}")
    elif zip_code is not None:
        url = f"{api_url}/zip?zip={zip_code}&appid={api_key}"
        configured_logger.info(f"Geocoding by zip code: {zip_code}")
    else:
        configured_logger.error("No location name or zip code provided.")
        raise ValueError(
            "You must provide either a location name or zip code for geocoding."
        )

    try:
        response = requests.get(url)
        configured_logger.info(f"API request sent to: {url}")

        if response.status_code == 200:
            data = response.json()
            if not data:
                configured_logger.warning("No matching locations found.")
                return {"error": "No matching locations found."}
            configured_logger.info(f"Successfully retrieved {len(data)} location(s).")
            return data
        else:
            configured_logger.error(f"Request failed with status code {response.status_code}.")
            return {"error": f"Request failed with status code {response.status_code}."}

    except Exception as e:
        configured_logger.error(f"Error during geocode_location request: {str(e)}")
        return {"error": f"An error occurred: {str(e)}"}


def get_geocode_location_tool():
    return StructuredTool.from_function(
        name="geocode_location",
        func=geocode_location,
        description=(
            " - Queries the OpenWeather Geocoding API to get geographical coordinates by location name or zip code.\n"
            "geocode_location(location_name: Optional[str], zip_code: Optional[str], limit: int) -> dict:\n"
            " - Returns a list of matching locations or an error message if no results are found.\n"
        ),
        input_schema=GeocodeLocationQuery,
    )
