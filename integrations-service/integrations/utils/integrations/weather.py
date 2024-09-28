from langchain_community.utilities import OpenWeatherMapAPIWrapper

from ...models import WeatherArguments, WeatherOutput, WeatherSetup


async def weather(setup: WeatherSetup, arguments: WeatherArguments) -> WeatherOutput:
    """
    Fetches weather data for a specified location using OpenWeatherMap API.
    """

    assert isinstance(setup, WeatherSetup), "Invalid setup"
    assert isinstance(arguments, WeatherArguments), "Invalid arguments"

    location = arguments.location

    openweathermap_api_key = setup.openweathermap_api_key
    if not location:
        raise ValueError("Location parameter is required for weather data")

    weather = OpenWeatherMapAPIWrapper(openweathermap_api_key=openweathermap_api_key)
    result = weather.run(location)
    return WeatherOutput(result=result)
