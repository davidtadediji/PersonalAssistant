import os

from pydantic import BaseModel, Field
from typing import Optional
import requests
from dotenv import load_dotenv
from langchain_core.tools import StructuredTool

load_dotenv()

class ReverseGeocodeQuery(BaseModel):
    lat: float = Field(..., description="The latitude coordinate.")
    lon: float = Field(..., description="The longitude coordinate.")
    limit: Optional[int] = Field(5, description="The number of location names to return (default is 5).")



def reverse_geocode( lat: float, lon: float, limit: int = 5) -> dict:
    api_key = os.getenv("OPENWEATHER_API_KEY")
    api_url = os.getenv("OPENWEATHER_REVERSE_GEOCODE_URL")

    url = f"{api_url}?lat={lat}&lon={lon}&limit={limit}&appid={api_key}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        if not data:
            return {"error": "No matching locations found."}
        return data
    else:
        return {"error": f"Request failed with status code {response.status_code}."}

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
