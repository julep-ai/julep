"""
Common database exception handling utilities.
"""

import inspect
import socket
from collections.abc import Callable
from functools import partialmethod, wraps

import asyncpg
import pydantic
from fastapi import HTTPException


def partialclass(cls, *args, **kwargs):
    cls_signature = inspect.signature(cls)
    bound = cls_signature.bind_partial(*args, **kwargs)

    # The `updated=()` argument is necessary to avoid a TypeError when using @wraps for a class
    @wraps(cls, updated=())
    class NewCls(cls):
        __init__ = partialmethod(cls.__init__, *bound.args, **bound.kwargs)

    return NewCls


def common_db_exceptions(
    resource_name: str,
    operations: list[str] | None = None,
) -> dict[
    type[BaseException] | Callable[[BaseException], bool],
    type[BaseException] | Callable[[BaseException], BaseException],
]:
    """
    Returns a mapping of common database exceptions to appropriate HTTP exceptions.
    This is commonly used with the @rewrap_exceptions decorator.

    Args:
        resource_name (str): The name of the resource being operated on (e.g. "agent", "task", "user")
        operations (list[str] | None, optional): List of operations being performed.
            Used to customize error messages. Defaults to None.

    Returns:
        dict: A mapping of database exceptions to HTTP exceptions
    """

    # Helper to format operation-specific messages
    def get_operation_message(base_msg: str) -> str:
        if not operations:
            return base_msg
        op_str = " or ".join(operations)
        return f"{base_msg} during {op_str}"

    exceptions = {
        # Foreign key violations - usually means a referenced resource doesn't exist
        asyncpg.ForeignKeyViolationError: partialclass(
            HTTPException,
            status_code=404,
            detail=get_operation_message(
                f"The specified {resource_name} or its dependencies do not exist"
            ),
        ),
        # Unique constraint violations - usually means a resource with same unique key exists
        asyncpg.UniqueViolationError: partialclass(
            HTTPException,
            status_code=409,
            detail=get_operation_message(
                f"A {resource_name} with these unique properties already exists"
            ),
        ),
        # Check constraint violations - usually means invalid data that violates DB constraints
        asyncpg.CheckViolationError: partialclass(
            HTTPException,
            status_code=400,
            detail=get_operation_message(
                f"The provided {resource_name} data violates one or more constraints"
            ),
        ),
        # Data type/format errors
        asyncpg.DataError: partialclass(
            HTTPException,
            status_code=400,
            detail=get_operation_message(f"Invalid {resource_name} data provided"),
        ),
        # No rows found for update/delete operations
        asyncpg.NoDataFoundError: partialclass(
            HTTPException,
            status_code=404,
            detail=get_operation_message(f"{resource_name.title()} not found"),
        ),
        # Connection errors (timeouts, etc)
        socket.gaierror: partialclass(
            HTTPException,
            status_code=429,
            detail="Resource busy. Please try again later.",
        ),
        # Invalid text representation
        asyncpg.InvalidTextRepresentationError: partialclass(
            HTTPException,
            status_code=400,
            detail=get_operation_message(f"Invalid text format in {resource_name} data"),
        ),
        # Numeric value out of range
        asyncpg.NumericValueOutOfRangeError: partialclass(
            HTTPException,
            status_code=400,
            detail=get_operation_message(
                f"Numeric value in {resource_name} data is out of allowed range"
            ),
        ),
        # String data right truncation
        asyncpg.StringDataRightTruncationError: partialclass(
            HTTPException,
            status_code=400,
            detail=get_operation_message(
                f"Text data in {resource_name} is too long for the field"
            ),
        ),
        # Not null violation
        asyncpg.NotNullViolationError: partialclass(
            HTTPException,
            status_code=400,
            detail=get_operation_message(f"Required {resource_name} field cannot be null"),
        ),
        # Python standard exceptions
        ValueError: partialclass(
            HTTPException,
            status_code=400,
            detail=get_operation_message(f"Invalid value provided for {resource_name}"),
        ),
        TypeError: partialclass(
            HTTPException,
            status_code=400,
            detail=get_operation_message(f"Invalid type for {resource_name}"),
        ),
        AttributeError: partialclass(
            HTTPException,
            status_code=404,
            detail=get_operation_message(f"Required attribute not found for {resource_name}"),
        ),
        KeyError: partialclass(
            HTTPException,
            status_code=404,
            detail=get_operation_message(f"Required key not found for {resource_name}"),
        ),
        # Pydantic validation errors
        pydantic.ValidationError: lambda e: partialclass(
            HTTPException,
            status_code=422,
            detail={
                "message": get_operation_message(f"Validation failed for {resource_name}"),
                "errors": [
                    {
                        "loc": list(error["loc"]),
                        "msg": error["msg"],
                        "type": error["type"],
                    }
                    for error in e.errors()
                ],
            },
        )(e),
    }

    # Add operation-specific exceptions
    if operations:
        if "delete" in operations:
            exceptions.update({
                # Handle cases where deletion is blocked by dependent records
                lambda e: isinstance(e, asyncpg.ForeignKeyViolationError)
                and "still referenced" in str(e): partialclass(
                    HTTPException,
                    status_code=409,
                    detail=f"Cannot delete {resource_name} because it is still referenced by other records",
                ),
            })

        if "update" in operations:
            exceptions.update({
                # Handle cases where update would affect multiple rows
                asyncpg.CardinalityViolationError: partialclass(
                    HTTPException,
                    status_code=409,
                    detail=f"Update would affect multiple {resource_name} records",
                ),
            })

    return exceptions
