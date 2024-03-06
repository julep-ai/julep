from asyncio import iscoroutinefunction
from functools import wraps
from typing import Callable
from uuid import UUID
from ..api.types import ResourceCreatedResponse


def is_valid_uuid4(uuid_to_test: str) -> bool:
    """
    Check if uuid_to_test is a valid UUID v4.

    Args:
        uuid_to_test (str): String to test for valid UUID v4.
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
        async def async_wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            return cls.construct(**kwargs, **result.dict())

        def sync_wrapper(*args, **kwargs):
            print(kwargs)  # Add this line to debug
            result = func(*args, **kwargs)
            return cls.construct(**kwargs, **result.dict())

        return async_wrapper if iscoroutinefunction(func) else sync_wrapper

    return decorator
