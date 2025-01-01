import os

from pydantic import BaseModel, Field
from typing import Optional
import requests
from langchain_core.tools import StructuredTool
from dotenv import load_dotenv

load_dotenv()

class GeocodeLocationQuery(BaseModel):
    location_name: Optional[str] = Field(None, description="The name of the location (e.g., 'London,GB').")
    zip_code: Optional[str] = Field(None, description="The zip/postal code (e.g., '90210,US').")
    limit: Optional[int] = Field(5, description="The number of locations to return (up to 5).")


def geocode_location(location_name: Optional[str] = None, zip_code: Optional[str] = None, limit: int = 5) -> dict:
    api_key = os.getenv("OPENWEATHER_API_KEY")
    api_url = os.getenv("OPENWEATHER_GEOCODE_URL")

    print(api_key)
    if location_name:
        url = f"{api_url}/direct?q={location_name}&limit={limit}&appid={api_key}"
    elif zip_code is not None:
        url = f"{api_url}/zip?zip={zip_code}&appid={api_key}"
    else:
        raise ValueError("You must provide either a location name or zip code for geocoding.")

    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        if not data:
            return {"error": "No matching locations found."}
        return data
    else:
        return {"error": f"Request failed with status code {response.status_code}."}

def get_geocode_location_tool():
    return StructuredTool.from_function(
        name="geocode_location",
        func=geocode_location,
        description=(
            "geocode_location(location_name: Optional[str], zip_code: Optional[str], limit: int) -> dict:\n"
            " - Queries the OpenWeather Geocoding API to get geographical coordinates by location name or zip code.\n"
            " - Returns a list of matching locations or an error message if no results are found.\n"
        ),
        input_schema=GeocodeLocationQuery,
    )
