"""This module provides JSON utilities, including a custom JSON encoder for handling specific object types and a utility function for JSON serialization."""

import json
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class CustomJSONEncoder(json.JSONEncoder):
    """A custom JSON encoder subclass that handles None values and UUIDs for JSON serialization. It allows specifying a default value for None objects during initialization."""

    def __init__(self, *args, **kwargs) -> None:
        """Initializes the custom JSON encoder.
        Parameters:
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments. The 'default_empty_value' keyword argument specifies the default value to use for None objects during serialization.
        """
        self._default_empty_value = kwargs.pop("default_empty_value")
        super().__init__(*args, **kwargs)

    def encode(self, o) -> str:
        """Encodes the given object into a JSON formatted string.
        Parameters:
        o: The object to encode.
        Returns: A JSON formatted string representing 'o'."""
        # Use the overridden default method for serialization before encoding
        return super().encode(self.default(o))

    def default(self, obj) -> Any:
        """Provides a default serialization for objects that the standard JSON encoder cannot serialize.
        Parameters:
        obj: The object to serialize.
        Returns: A serializable object or raises a TypeError if the object is not serializable.
        """
        if obj is None:
            return self._default_empty_value

        if isinstance(obj, UUID):
            return str(obj)

        if isinstance(obj, BaseModel):
            return obj.model_dump()

        return obj


def dumps(obj: Any, default_empty_value="", cls=None) -> str:
    """Serializes an object to a JSON formatted string using the custom JSON encoder.
    Parameters:
    obj: The object to serialize.
    default_empty_value: The default value to use for None objects.
    cls: The custom encoder class to use, defaults to CustomJSONEncoder.
    Returns: A JSON formatted string."""
    return json.dumps(
        obj, cls=cls or CustomJSONEncoder, default_empty_value=default_empty_value
    )
