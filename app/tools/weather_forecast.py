import os
from typing import Dict, Optional

import requests
from dotenv import load_dotenv
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from typing_extensions import Literal
from typing import Any

# Load environment variables
load_dotenv()


class OpenWeather:
    """OpenWeather One Call API 3.0 client."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = os.getenv("OPENWEATHER_API_URL")

    def _validate_coordinates(self, lat: float, lon: float) -> None:
        """Validate latitude and longitude values."""
        if not (-90 <= lat <= 90):
            raise ValueError("Latitude must be between -90 and 90")
        if not (-180 <= lon <= 180):
            raise ValueError("Longitude must be between -180 and 180")

    def get_current_and_forecast(
        self, lat: float, lon: float, units: Literal["standard", "metric", "imperial"] = "standard", lang: str = "en"
    ) -> Dict[str, Any]:
        """Get current weather and forecast."""
        self._validate_coordinates(lat, lon)
        query_params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key,
            "units": units,
            "lang": lang,
        }
        response = requests.get(self.base_url, params=query_params)
        response.raise_for_status()
        return response.json()


class WeatherForecastQuery(BaseModel):
    lat: float = Field(
        ..., ge=-90, le=90, description="Latitude of the location (range: -90 to 90)."
    )
    lon: float = Field(
        ..., ge=-180, le=180, description="Longitude of the location (range: -180 to 180)."
    )
    units: Literal["standard", "metric", "imperial"] = Field(
        "standard",
        description=(
            "Units of measurement. Options: "
            "'standard' (Kelvin, m/s), 'metric' (Celsius, m/s), 'imperial' (Fahrenheit, mph)."
        ),
    )
    lang: Optional[str] = Field(
        "en",
        description="Language code for descriptions (e.g., 'en', 'es', 'fr'). Default is 'en'.",
    )


def weather_forecast(
    lat: float, lon: float, units: Literal["standard", "metric", "imperial"] = "standard", lang: str = "en"
) -> Dict[str, Any]:
    """Fetch current weather and forecast using OpenWeather One Call API 3.0."""
    client = OpenWeather(os.getenv("OPENWEATHER_API_KEY"))
    return client.get_current_and_forecast(lat, lon, units, lang)


def get_weather_forecast_tool() -> StructuredTool:
    """
    Returns a StructuredTool for the weather_forecast function.

    Returns:
        StructuredTool: Tool for fetching current weather and forecast data.
    """
    return StructuredTool.from_function(
        name="weather_forecast",
        func=weather_forecast,
        description=(
            "Fetches current weather and forecast data from OpenWeather One Call API 3.0.\n"
            "weather_forecast(lat: float, lon: float, units: Literal['standard', 'metric', 'imperial'], lang: str)"
            "Parameters:\n"
            "lat (float): Latitude (-90 to 90).\n"
            "lon (float): Longitude (-180 to 180).\n"
            "units (Literal): Measurement units. Options: 'standard' (Kelvin, m/s), 'metric' (Celsius, m/s), 'imperial' (Fahrenheit, mph).\n"
            "lang (str, optional): Language. Default is 'en'.\n"
            "Returns:\n"
            "A dictionary with the current weather and forecast information."
        ),
        input_schema=WeatherForecastQuery,
    )