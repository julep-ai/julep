from typing import Any, Callable

from fastapi import Request


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


def create_filter_extractor(
    prefix: str = "filter",
) -> Callable[[Request], dict[str, Any]]:
    """
    Creates a dependency function to extract filter parameters with a given prefix.

    Args:
        prefix (str): The prefix to identify filter parameters.

    Returns:
        Callable[[Request], dict[str, Any]]: The dependency function.
    """

    # Add a dot to the prefix to allow for nested filters
    prefix += "."

    def extract_filters(request: Request) -> dict[str, Any]:
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

        return filters

    return extract_filters
