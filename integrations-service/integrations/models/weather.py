from pydantic import Field

from .base_models import (
    BaseArguments,
    BaseOutput,
    BaseSetup,
)


class WeatherSetup(BaseSetup):
    openweathermap_api_key: str = Field(
        ..., description="The api key for OpenWeatherMap"
    )


class WeatherGetArguments(BaseArguments):
    location: str = Field(
        ..., description="The location for which to fetch weather data"
    )


class WeatherGetOutput(BaseOutput):
    result: str = Field(..., description="The weather data for the specified location")
