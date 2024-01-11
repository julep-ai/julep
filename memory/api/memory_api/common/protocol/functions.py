from enum import Enum
from typing import Any, Optional, TypedDict

from pydantic import BaseModel


class JsonSchemaType(str, Enum):
    """An enumeration of JSON Schema type values."""

    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"
    NULL = "null"
    ANY = "any"


class ItemsDict(BaseModel):
    """JSON Schema representation of array items."""

    type: JsonSchemaType


class PropertyDict(BaseModel):
    """JSON Schema representation of a parameter."""

    type: JsonSchemaType
    description: Optional[str] = None
    enum: Optional[list[Any]] = None
    items: Optional[ItemsDict] = None


class ParametersDict(BaseModel):
    """A JSON schema representation of a parameter object."""

    type: JsonSchemaType
    properties: dict[str, PropertyDict]
    required: Optional[list[str]] = None
