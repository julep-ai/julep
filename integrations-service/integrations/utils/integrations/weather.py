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

    location = arguments.location

    # Use walrus operator to simplify assignment and condition
    if (api_key := setup.openweathermap_api_key) == "DEMO_API_KEY":
        api_key = openweather_api_key

    weather = OpenWeatherMapAPIWrapper(openweathermap_api_key=api_key)
    result = weather.run(location)
    return WeatherGetOutput(result=result)
