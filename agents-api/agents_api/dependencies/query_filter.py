from typing import Any, Callable

from fastapi import Request
from pydantic import BaseModel


class FilterModel(BaseModel):
    class Config:
        extra = "allow"  # Allow arbitrary fields


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


def create_filter_extractor(prefix: str = "filter") -> Callable[[Request], FilterModel]:
    """
    Creates a dependency function to extract filter parameters with a given prefix.

    Args:
        prefix (str): The prefix to identify filter parameters.

    Returns:
        Callable[[Request], FilterModel]: The dependency function.
    """

    def extract_filters(request: Request) -> FilterModel:
        """
        Extracts query parameters that start with the specified prefix and returns them as a dictionary.

        Args:
            request (Request): The incoming HTTP request.

        Returns:
            FilterModel: A FilterModel instance containing the filter parameters.
        """
        nonlocal prefix
        prefix += "."

        filters: dict[str, Any] = {}
        for key, value in request.query_params.items():
            if key.startswith(prefix):
                filter_key = key[len(prefix) :]
                filters[filter_key] = convert_value(value)

        return FilterModel(**filters)

    return extract_filters
