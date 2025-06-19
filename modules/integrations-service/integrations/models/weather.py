from pydantic import Field

from .base_models import BaseOutput


class WeatherGetOutput(BaseOutput):
    result: str = Field(..., description="The weather data for the specified location")
