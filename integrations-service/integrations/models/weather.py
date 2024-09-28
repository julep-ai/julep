from pydantic import Field

from .base_models import (
    BaseArguments,
    BaseOutput,
    BaseProvider,
    BaseProviderMethod,
    BaseSetup,
    ProviderInfo,
)


class WeatherSetup(BaseSetup):
    openweathermap_api_key: str = Field(
        ..., description="The api key for OpenWeatherMap"
    )


class WeatherArguments(BaseArguments):
    location: str = Field(
        ..., description="The location for which to fetch weather data"
    )


class WeatherOutput(BaseOutput):
    result: str = Field(..., description="The weather data for the specified location")


weather_provider = BaseProvider(
    provider="openweathermap",
    setup=WeatherSetup.model_json_schema(),
    methods=[
        BaseProviderMethod(
            method="get_weather",
            description="Get the weather for a given location",
            arguments=WeatherArguments.model_json_schema(),
            output=WeatherOutput.model_json_schema(),
        )
    ],
    info=ProviderInfo(
        url="https://openweathermap.org/",
        docs="https://openweathermap.org/api",
        icon="https://openweathermap.org/img/wn/01d@2x.png",
        friendly_name="Weather",
    ),
)
