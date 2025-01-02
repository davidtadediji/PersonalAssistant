from typing import Optional

import geocoder
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class CurrentLocationQuery(BaseModel):
    nothing: Optional[str] = Field(
        None, description="This argument is not used for anything')."
    )


def get_current_location(nothing: Optional[str]) -> dict:
    g = geocoder.ip("me")  # Uses IP address to find the location
    return g.json


def get_current_location_tool():
    return StructuredTool.from_function(
        name="get_current_location",
        func=get_current_location,
        description=(
            "get_current_location(nothing : Optional[str]) -> dict:\n"
            " - Returns the current location based on the IP address, including city, country, latitude, and longitude.\n"
        ),
        input_schema=CurrentLocationQuery,
    )
