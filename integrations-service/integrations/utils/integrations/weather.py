import os

from langchain_community.utilities import OpenWeatherMapAPIWrapper

from ...models import WeatherExecutionArguments, WeatherExecutionSetup


async def weather(
    setup: WeatherExecutionSetup, arguments: WeatherExecutionArguments
) -> str:
    """
    Fetches weather data for a specified location using OpenWeatherMap API.
    """
    location = arguments.location

    openweathermap_api_key = setup.openweathermap_api_key
    if not location:
        raise ValueError("Location parameter is required for weather data")

    weather = OpenWeatherMapAPIWrapper(openweathermap_api_key=openweathermap_api_key)

    return weather.run(location)
