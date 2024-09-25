from pydantic import BaseModel, Field


class WeatherExecutionSetup(BaseModel):
    openweathermap_api_key: str = Field(
        ..., description="The location for which to fetch weather data"
    )


class WeatherExecutionArguments(BaseModel):
    location: str = Field(
        ..., description="The location for which to fetch weather data"
    )
