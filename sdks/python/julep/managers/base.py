from typing import Union

from ..client import JulepApi, AsyncJulepApi


# Purpose: Base class for all managers
class BaseManager:
    """
    A class that serves as a base manager for working with different API clients. This class is responsible for abstracting the complexities of interacting with various API clients, providing a unified interface for higher-level components.

        Attributes:
            api_client (Union[JulepApi, AsyncJulepApi]): A client instance for communicating with an API. This attribute is essential for enabling the class to perform API operations, whether they are synchronous or asynchronous.

        Args:
            api_client (Union[JulepApi, AsyncJulepApi]): The API client that is used for making API calls. It is crucial for the operation of this class, allowing it to interact with the API effectively.
    """

    api_client: Union[JulepApi, AsyncJulepApi]

    def __init__(self, api_client: Union[JulepApi, AsyncJulepApi]):
        """
        Constructor for the class that initializes it with an API client.

        Args:
            api_client (Union[JulepApi, AsyncJulepApi]): An instance of JulepApi or AsyncJulepApi to be used by this class.
        """
        self.api_client = api_client
