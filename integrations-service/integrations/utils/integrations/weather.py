from langchain_community.utilities import OpenWeatherMapAPIWrapper

from ...models import WeatherGetArguments, WeatherGetOutput, WeatherSetup


async def get(setup: WeatherSetup, arguments: WeatherGetArguments) -> WeatherGetOutput:
    """
    Fetches weather data for a specified location using OpenWeatherMap API.
    """

    assert isinstance(setup, WeatherSetup), "Invalid setup"
    assert isinstance(arguments, WeatherGetArguments), "Invalid arguments"

    location = arguments.location

    openweathermap_api_key = setup.openweathermap_api_key
    if not location:
        raise ValueError("Location parameter is required for weather data")

    weather = OpenWeatherMapAPIWrapper(openweathermap_api_key=openweathermap_api_key)
    result = weather.run(location)
    return WeatherGetOutput(result=result)

