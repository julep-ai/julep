from beartype import beartype
from langchain_community.utilities import OpenWeatherMapAPIWrapper
from tenacity import retry, stop_after_attempt, wait_exponential

from ...autogen.Tools import WeatherGetArguments, WeatherSetup
from ...env import openweather_api_key  # Import env to access environment variables
from ...models import WeatherGetOutput


@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    stop=stop_after_attempt(4),
)
async def get(setup: WeatherSetup, arguments: WeatherGetArguments) -> WeatherGetOutput:
    """
    Fetches weather data for a specified location using OpenWeatherMap API.
    """

    assert isinstance(setup, WeatherSetup), "Invalid setup"
    assert isinstance(arguments, WeatherGetArguments), "Invalid arguments"

    location = arguments.location

    openweathermap_api_key = setup.openweathermap_api_key
    if openweathermap_api_key == "DEMO_API_KEY":
        openweathermap_api_key = openweather_api_key

    if not location:
        raise ValueError("Location parameter is required for weather data")

    weather = OpenWeatherMapAPIWrapper(openweathermap_api_key=openweathermap_api_key)
    result = weather.run(location)
    return WeatherGetOutput(result=result)
