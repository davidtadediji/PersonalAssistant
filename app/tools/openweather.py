import os
from enum import Enum
from typing import Optional, List, Dict, Any

import requests
from dotenv import load_dotenv

load_dotenv()


class Units(Enum):
    STANDARD = "standard"  # Kelvin, m/s
    METRIC = "metric"  # Celsius, m/s
    IMPERIAL = "imperial"  # Fahrenheit, mph


class OpenWeather:
    """OpenWeather One Call API 3.0 client"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = os.getenv("OPENWEATHER_API_URL")

    def _validate_coordinates(self, lat: float, lon: float) -> None:
        """Validate latitude and longitude values"""
        if not (-90 <= lat <= 90):
            raise ValueError("Latitude must be between -90 and 90")
        if not (-180 <= lon <= 180):
            raise ValueError("Longitude must be between -180 and 180")

    def get_current_forecast(
        self,
        lat: float,
        lon: float,
        units: str = "standard",
        lang: str = "en",
        exclude: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get current weather and forecast data

        Args:
            lat: Latitude between -90 and 90
            lon: Longitude between -180 and 180
            units: Units of measurement ("standard", "metric", or "imperial")
            lang: Language code (e.g., "en", "es", "fr")
            exclude: List of data to exclude from response ("current", "minutely", "hourly", "daily", "alerts")

        Returns:
            Dict containing current weather and forecast data
        """
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

        response = requests.get(self.base_url, params=query_params)
        response.raise_for_status()
        return response.json()

    def get_historical(
        self,
        lat: float,
        lon: float,
        timestamp: int,
        units: str = "standard",
        lang: str = "en",
    ) -> Dict[str, Any]:
        """Get historical weather data for a specific timestamp

        Args:
            lat: Latitude between -90 and 90
            lon: Longitude between -180 and 180
            timestamp: Unix timestamp (UTC) for historical data
            units: Units of measurement ("standard", "metric", or "imperial")
            lang: Language code (e.g., "en", "es", "fr")

        Returns:
            Dict containing historical weather data
        """
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

        response = requests.get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def get_daily_aggregate(
        self,
        lat: float,
        lon: float,
        date: str,
        timezone: Optional[str] = None,
        units: str = "standard",
        lang: str = "en",
    ) -> Dict[str, Any]:
        """Get daily aggregated weather data

        Args:
            lat: Latitude between -90 and 90
            lon: Longitude between -180 and 180
            date: Date in YYYY-MM-DD format
            timezone: Optional timezone in ±XX:XX format
            units: Units of measurement ("standard", "metric", or "imperial")
            lang: Language code (e.g., "en", "es", "fr")

        Returns:
            Dict containing daily aggregated weather data
        """
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

        response = requests.get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def get_overview(
        self,
        lat: float,
        lon: float,
        date: Optional[str] = None,
        units: str = "standard",
    ) -> Dict[str, Any]:
        """Get weather overview with AI-generated summary

        Args:
            lat: Latitude between -90 and 90
            lon: Longitude between -180 and 180
            date: Optional date in YYYY-MM-DD format (today or tomorrow only)
            units: Units of measurement ("standard", "metric", or "imperial")

        Returns:
            Dict containing weather overview and AI-generated summary
        """
        self._validate_coordinates(lat, lon)

        url = f"{self.base_url}/overview"
        query_params = {"lat": lat, "lon": lon, "appid": self.api_key, "units": units}

        if date:
            query_params["date"] = date

        response = requests.get(url, params=query_params)
        response.raise_for_status()
        return response.json()
