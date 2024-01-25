from typing import Union

from ..client import JulepApi, AsyncJulepApi


# Purpose: Base class for all managers
class BaseManager:
    """
    A class that serves as a base manager for working with different API clients.

        Attributes:
            api_client (Union[JulepApi, AsyncJulepApi]): A client instance for communicating with an API.
                It can either be an instance of JulepApi for synchronous operations or
                AsyncJulepApi for asynchronous operations.

        Args:
            api_client (Union[JulepApi, AsyncJulepApi]): The API client that is used for making API calls.
    """

    api_client: Union[JulepApi, AsyncJulepApi]

    def __init__(self, api_client: Union[JulepApi, AsyncJulepApi]):
        """
        Constructor for the class that initializes it with an API client.

        Args:
            api_client (Union[JulepApi, AsyncJulepApi]): An instance of JulepApi or AsyncJulepApi to be used by this class.
        """
        self.api_client = api_client
