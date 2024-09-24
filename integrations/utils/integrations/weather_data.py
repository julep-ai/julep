import os
from langchain_community.utilities import OpenWeatherMapAPIWrapper


async def weather_data(parameters: dict) -> str:
    """
    Fetches weather data for a specified location using OpenWeatherMap API.
    """
    location = parameters.get("location")

    openweathermap_api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    if not location:
        raise ValueError("Location parameter is required for weather data")

    weather = OpenWeatherMapAPIWrapper(
        openweathermap_api_key=openweathermap_api_key)

    return weather.run(location)
