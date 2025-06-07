from beartype import beartype
from langchain_community.utilities import OpenWeatherMapAPIWrapper
from tenacity import retry, stop_after_attempt, wait_exponential

from ...autogen.Tools import WeatherGetArguments, WeatherSetup
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

    weather = OpenWeatherMapAPIWrapper(openweathermap_api_key=setup.openweathermap_api_key)
    result = weather.run(location)
    return WeatherGetOutput(result=result)
