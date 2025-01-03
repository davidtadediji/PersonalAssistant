from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
import os
from app.tools.openweather import OpenWeather


class WeatherForecastInput(BaseModel):
    operation: str = Field(
        ..., 
        description="The type of weather data to retrieve. Options: 'current_forecast', 'historical', 'daily_aggregate', 'overview'."
    )
    lat: float = Field(..., description="Latitude between -90 and 90.")
    lon: float = Field(..., description="Longitude between -180 and 180.")
    units: str = Field(
        default="standard", 
        description="Units of measurement. Options: 'standard', 'metric', 'imperial'."
    )
    lang: str = Field(
        default="en", 
        description="Language code for the response (e.g., 'en', 'es', 'fr')."
    )
    exclude: Optional[List[str]] = Field(
        None, 
        description="List of data parts to exclude for 'current_forecast' operation (e.g., 'minutely', 'hourly')."
    )
    timestamp: Optional[int] = Field(
        None, 
        description="Unix timestamp required for 'historical' operation."
    )
    date: Optional[str] = Field(
        None, 
        description="Date in 'YYYY-MM-DD' format, required for 'daily_aggregate' and optional for 'overview'."
    )
    timezone: Optional[str] = Field(
        None, 
        description="Timezone in ±HH:MM format, optional for 'daily_aggregate' operation."
    )

def weather_forecast(
    operation: str,
    lat: float,
    lon: float,
    units: str = "standard",
    lang: str = "en",
    exclude: Optional[List[str]] = None,
    timestamp: Optional[int] = None,
    date: Optional[str] = None,
    timezone: Optional[str] = None,
) -> Dict[str, Any]:
    # OpenWeather client setup
    client = OpenWeather(os.getenv("OPENWEATHER_API_KEY"))

    if operation == "current_forecast":
        return client.get_current_forecast(lat, lon, units, lang, exclude)
    elif operation == "historical":
        if timestamp is None:
            raise ValueError("Timestamp is required for historical operation")
        return client.get_historical(lat, lon, timestamp, units, lang)
    elif operation == "daily_aggregate":
        if date is None:
            raise ValueError("Date is required for daily_aggregate operation")
        return client.get_daily_aggregate(lat, lon, date, timezone, units, lang)
    elif operation == "overview":
        return client.get_overview(lat, lon, date, units)
    else:
        raise ValueError(f"Unknown operation: {operation}")

from langchain.tools import StructuredTool

def get_weather_forecast_tool():
    return StructuredTool.from_function(
        name="weather_forecast",
        func=weather_forecast,
        description=(
            """   Get weather information from OpenWeather One Call API 3.0

    Args:
        operation: Type of weather data to retrieve:
            - "current_forecast": Current weather and forecast data
            - "historical": Historical weather data
            - "daily_aggregate": Daily aggregated weather data
            - "overview": Weather overview with AI summary
        lat: Latitude between -90 and 90
        lon: Longitude between -180 and 180
        units: Units of measurement ("standard", "metric", or "imperial")
        lang: Language code (e.g., "en", "es", "fr")
        exclude: List of data to exclude for current_forecast (optional)
        timestamp: Unix timestamp for historical data (required for historical operation)
        date: Date in YYYY-MM-DD format (required for daily_aggregate, optional for overview)
        timezone: Timezone in ±XX:XX format (optional, for daily_aggregate only)

    Returns:
        Dict containing requested weather information

    Example:
        # Get current weather
        result = weather_information(
            operation="current_forecast",
            lat=33.44,
            lon=-94.04,
            api_key="your_api_key",
            units="metric"
        )

        # Get historical weather
        result = weather_information(
            operation="historical",
            lat=33.44,
            lon=-94.04,
            api_key="your_api_key",
            timestamp=1643803200
        )""" ),
        input_schema=WeatherForecastInput,
    )
