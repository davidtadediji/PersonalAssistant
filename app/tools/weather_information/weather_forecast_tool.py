import os
from enum import Enum
from typing import Optional, List, Dict
import requests
from dotenv import load_dotenv
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field, validator
from typing import  Any

from app.logger import configured_logger

# Load environment variables
load_dotenv()


class Units(Enum):
    STANDARD = "standard"  # Kelvin, m/s
    METRIC = "metric"  # Celsius, m/s
    IMPERIAL = "imperial"  # Fahrenheit, mph


class OpenWeather:
    """OpenWeather One Call API 3.0 client."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = os.getenv("OPENWEATHER_API_URL")
        configured_logger.info(f"OpenWeather client initialized with API URL: {self.base_url}")

    def _validate_coordinates(self, lat: float, lon: float) -> None:
        """Validate latitude and longitude values."""
        configured_logger.info(f"Validating coordinates: lat={lat}, lon={lon}")
        if not (-90 <= lat <= 90):
            configured_logger.error("Latitude must be between -90 and 90")
            raise ValueError("Latitude must be between -90 and 90")
        if not (-180 <= lon <= 180):
            configured_logger.error("Longitude must be between -180 and 180")
            raise ValueError("Longitude must be between -180 and 180")

    def get_current_and_forecast(self, lat: float, lon: float, exclude: Optional[List[str]] = None,
                                 units: str = "standard", lang: str = "en") -> Dict[str, Any]:
        """Get current weather, minute forecast for 1 hour, hourly forecast for 48 hours, daily forecast for 8 days, and government weather alerts."""
        try:
            self._validate_coordinates(lat, lon)
            query_params = {
                "lat": lat,
                "lon": lon,
                "appid": self.api_key,
                "units": units,
                "lang": lang,
            }
            if exclude:
                query_params["exclude"] = ",".join(exclude)
            configured_logger.info(f"Making request with params: {query_params}")
            response = requests.get(self.base_url, params=query_params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            configured_logger.error(f"Error fetching current and forecast data: {str(e)}")
            raise

    def get_historical(self, lat: float, lon: float, timestamp: int, units: str = "standard", lang: str = "en") -> Dict[
        str, Any]:
        """Get historical weather data for a specific timestamp."""
        try:
            self._validate_coordinates(lat, lon)
            url = f"{self.base_url}/timemachine"
            query_params = {
                "lat": lat,
                "lon": lon,
                "dt": timestamp,
                "appid": self.api_key,
                "units": units,
                "lang": lang,
            }
            configured_logger.info(f"Making request to {url} with params: {query_params}")
            response = requests.get(url, params=query_params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            configured_logger.error(f"Error fetching historical data: {str(e)}")
            raise

    def get_daily_aggregate(self, lat: float, lon: float, date: str, timezone: Optional[str] = None,
                            units: str = "standard", lang: str = "en") -> Dict[str, Any]:
        """Get daily aggregated weather data for a specific date."""
        try:
            self._validate_coordinates(lat, lon)
            url = f"{self.base_url}/day_summary"
            query_params = {
                "lat": lat,
                "lon": lon,
                "date": date,
                "appid": self.api_key,
                "units": units,
                "lang": lang,
            }
            if timezone:
                query_params["tz"] = timezone
            configured_logger.info(f"Making request to {url} with params: {query_params}")
            response = requests.get(url, params=query_params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            configured_logger.error(f"Error fetching daily aggregate data: {str(e)}")
            raise

    def get_weather_overview(self, lat: float, lon: float, date: Optional[str] = None, units: str = "standard") -> Dict[
        str, Any]:
        """Get a weather overview with a human-readable summary for today or tomorrow's forecast."""
        try:
            self._validate_coordinates(lat, lon)
            url = f"{self.base_url}/overview"
            query_params = {
                "lat": lat,
                "lon": lon,
                "appid": self.api_key,
                "units": units,
            }
            if date:
                query_params["date"] = date
            configured_logger.info(f"Making request to {url} with params: {query_params}")
            response = requests.get(url, params=query_params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            configured_logger.error(f"Error fetching weather overview: {str(e)}")
            raise


# Example for logging in weather_forecast function

def weather_forecast(operation: str, lat: float, lon: float, units: str = "standard", lang: str = "en",
                     exclude: Optional[List[str]] = None, timestamp: Optional[int] = None, date: Optional[str] = None,
                     timezone: Optional[str] = None) -> Dict[str, Any]:
    """Fetch weather information using OpenWeather One Call API 3.0."""
    try:
        configured_logger.info(
            f"Fetching weather forecast for operation={operation}, lat={lat}, lon={lon}, units={units}, lang={lang}")
        # Ensure lat and lon are floats
        lat = float(lat)
        lon = float(lon)

        client = OpenWeather(os.getenv("OPENWEATHER_API_KEY"))

        # Ensure timestamp is None if not provided or invalid
        if timestamp == "None" or timestamp == "":
            timestamp = None

        if operation == "current_forecast":
            return client.get_current_and_forecast(lat, lon, exclude, units, lang)
        elif operation == "historical":
            if timestamp is None:
                raise ValueError("Timestamp is required for historical operation")
            return client.get_historical(lat, lon, timestamp, units, lang)
        elif operation == "daily_aggregate":
            if date is None:
                raise ValueError("Date is required for daily_aggregate operation")
            return client.get_daily_aggregate(lat, lon, date, timezone, units, lang)
        elif operation == "overview":
            return client.get_weather_overview(lat, lon, date, units)
        else:
            raise ValueError(f"Unknown operation: {operation}")
    except Exception as e:
        configured_logger.error(f"Error during weather forecast operation: {str(e)}")
        raise


class WeatherForecastQuery(BaseModel):
    operation: str = Field(
        ...,
        description=(
            "Specifies the type of weather data to retrieve. "
            "Options: 'current_forecast', 'historical', 'daily_aggregate', or 'overview'."
        ),
    )
    lat: float = Field(
        ..., ge=-90, le=90, description="Latitude of the location (range: -90 to 90)."
    )
    lon: float = Field(
        ...,
        ge=-180,
        le=180,
        description="Longitude of the location (range: -180 to 180).",
    )
    units: Optional[str] = Field(
        "standard",
        description=(
            "Units of measurement. Options: "
            "'standard' (default), 'metric' (Celsius, m/s), 'imperial' (Fahrenheit, mph)."
        ),
    )
    lang: Optional[str] = Field(
        "en",
        description="Language code for descriptions (e.g., 'en', 'es', 'fr'). Default is 'en'.",
    )
    exclude: Optional[List[str]] = Field(
        None,
        description="List of data blocks to exclude for 'current_forecast' (e.g., ['minutely', 'alerts']).",
    )
    timestamp: Optional[int] = Field(
        None,
        description="Unix timestamp for historical data. Required for 'historical' operation.",
    )
    date: Optional[str] = Field(
        None,
        pattern=r"\d{4}-\d{2}-\d{2}",
        description="Date in 'YYYY-MM-DD' format. Required for 'daily_aggregate' and optional for 'overview'.",
    )
    timezone: Optional[str] = Field(
        None,
        pattern=r"^[+-](0[0-9]|1[0-4]):[0-5][0-9]$",
        description="Timezone in ±HH:MM format. Used for 'daily_aggregate' operation.",
    )

    @validator("operation")
    def validate_operation(cls, v):
        valid_operations = [
            "current_forecast",
            "historical",
            "daily_aggregate",
            "overview",
        ]
        if v not in valid_operations:
            raise ValueError(f"Invalid operation. Must be one of: {valid_operations}")
        return v


def get_weather_forecast_tool() -> StructuredTool:
    """
    Returns a StructuredTool for the weather_forecast function.

    Returns:
        StructuredTool: Tool for fetching weather data.
    """
    return StructuredTool.from_function(
        name="weather_forecast",
        func=weather_forecast,
        description=(
            "weather_forecast(operation: str, lat: float, lon: float, units: Optional[str], lang: Optional[str], exclude: Optional[list], timestamp: Optional[int], date: Optional[str], timezone: Optional[str]) -> dict:\n"
            " - Retrieves detailed weather information from the OpenWeather One Call API 3.0.\n"
            " - **operation** (str): Specifies the type of weather data to retrieve:\n"
            "    - 'current_forecast': Provides current weather and forecast data.\n"
            "    - 'historical': Retrieves historical weather data. Requires `timestamp`.\n"
            "    - 'daily_aggregate': Fetches daily aggregated weather data. Requires `date` and optionally `timezone`.\n"
            "    - 'overview': Generates a weather overview with an AI-generated summary. Accepts `date` (optional).\n"
            " - **lat** (float): Latitude of the location (range: -90 to 90).\n"
            " - **lon** (float): Longitude of the location (range: -180 to 180).\n"
            " - **units** (str, optional): Units of measurement. Options:\n"
            "    - 'standard': Default units.\n"
            "    - 'metric': Celsius for temperature, meters/second for wind speed.\n"
            "    - 'imperial': Fahrenheit for temperature, miles/hour for wind speed.\n"
            " - **lang** (str, optional): Language code for descriptions (e.g., 'en', 'es', 'fr'). Default is 'en'.\n"
            " - **exclude** (list, optional): List of data blocks to exclude from `current_forecast` (e.g., ['minutely', 'alerts']).\n"
            " - **timestamp** (int, optional): Unix timestamp for historical data. Required for 'historical' operation.\n"
            " - **date** (str, optional): Date in 'YYYY-MM-DD' format. Required for 'daily_aggregate' and optional for 'overview'.\n"
            " - **timezone** (str, optional): Timezone in ±HH:MM format. Used for 'daily_aggregate' operation.\n"
            " - Returns a dictionary containing the requested weather information.\n"
        ),
        input_schema=WeatherForecastQuery,
    )


from langchain_core.tools import StructuredTool
from pydantic import BaseModel
from typing import Dict


class WeatherForecastMockQuery(BaseModel):
    location: str  # Now accepts a simple string


def weather_information(location: str) -> Dict[str, str]:
    """Mock function to simulate current weather forecast retrieval."""
    # Example of mock data based on location string
    mock_data = f"Current weather at {location}: Clear skies, 25°C."
    return {"location": location, "data": mock_data}


def get_weather_information_tool():
    return StructuredTool.from_function(
        name="weather_information",
        func=weather_information,
        description=(
            "weather_information(location: str) -> dict:\n"
            " - Returns the current weather at the given location as a string. The location should be provided as a name (e.g., 'New York, USA').\n"
        ),
        input_schema=WeatherForecastMockQuery,
    )
