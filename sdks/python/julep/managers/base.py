from typing import Union

from ..client import JulepApi, AsyncJulepApi


# Purpose: Base class for all managers
class BaseManager:
    api_client: Union[JulepApi, AsyncJulepApi]

    def __init__(self, api_client: Union[JulepApi, AsyncJulepApi]):
        self.api_client = api_client
