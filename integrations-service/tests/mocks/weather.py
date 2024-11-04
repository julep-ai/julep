"""Mock implementation of weather API client"""


class MockWeatherClient:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_weather(self, location: str) -> str:
        """Mock weather lookup that returns fixed data"""
        return f"Mock weather data for {location}: Sunny, 72°F"


class MockWeatherException(Exception):
    """Mock exception for weather API errors"""

    pass
