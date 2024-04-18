from asyncio import iscoroutinefunction
from functools import wraps
from typing import Callable
from uuid import UUID
from ..api.types import ResourceCreatedResponse


class NotSet:
    pass


NotSet = NotSet()


def is_valid_uuid4(uuid_to_test: str) -> bool:
    """
    Check if uuid_to_test is a valid UUID v4.

    Args:
        uuid_to_test (str): String to test for valid UUID v4.

    This function can also directly check UUID instances to confirm they are version 4.
    """

    if isinstance(uuid_to_test, UUID):
        return uuid_to_test.version == 4

    try:
        _ = UUID(uuid_to_test, version=4)
    except ValueError:
        return False

    return True


def rewrap_in_class(cls):
    def decorator(func: Callable[..., ResourceCreatedResponse]):
        @wraps(func)
        # This wrapper is used for asynchronous functions to ensure they are properly awaited and their results are processed by `cls.construct`.
        async def async_wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            return cls.construct(**kwargs, **result.dict())

        # This wrapper handles synchronous functions, directly calling them and processing their results with `cls.construct`.
        def sync_wrapper(*args, **kwargs):
            # Logging at this point might be useful for debugging, but should use a proper logging framework instead of print statements for production code.
            result = func(*args, **kwargs)
            return cls.construct(**kwargs, **result.dict())

        return async_wrapper if iscoroutinefunction(func) else sync_wrapper

    return decorator
