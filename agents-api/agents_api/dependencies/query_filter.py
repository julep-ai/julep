from typing import Annotated, Any, Callable

from fastapi import Query, Request
from pydantic import BaseModel, ConfigDict


def convert_value(value: str) -> Any:
    """
    Attempts to convert a string value to an int or float. Returns the original string if conversion fails.
    """
    for convert in (int, float):
        try:
            return convert(value)
        except ValueError:
            continue
    return value


class MetadataFilter(BaseModel):
    model_config = ConfigDict(extra="allow")


def create_filter_extractor(
    prefix: str = "metadata_filter",
) -> Callable[[Request, MetadataFilter], MetadataFilter]:
    """
    Creates a dependency function to extract filter parameters with a given prefix.

    Args:
        prefix (str): The prefix to identify filter parameters.

    Returns:
        Callable[[Request], dict[str, Any]]: The dependency function.
    """

    # Add a dot to the prefix to allow for nested filters
    prefix += "."

    def extract_filters(
        request: Request,
        metadata_filter: Annotated[
            MetadataFilter, Query(default_factory=MetadataFilter)
        ],
    ) -> MetadataFilter:
        """
        Extracts query parameters that start with the specified prefix and returns them as a dictionary.

        Args:
            request (Request): The incoming HTTP request.

        Returns:
            dict[str, Any]: A dictionary containing the filter parameters.
        """

        filters: dict[str, Any] = {}

        for key, value in request.query_params.items():
            if key.startswith(prefix):
                filter_key = key[len(prefix) :]
                filters[filter_key] = convert_value(value)

        return MetadataFilter(**filters)

    return extract_filters
