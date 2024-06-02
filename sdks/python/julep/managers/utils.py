from asyncio import iscoroutinefunction
from functools import wraps
from typing import Callable
from uuid import UUID
from typing_extensions import ParamSpec

from pydantic.main import Model

from ..api.types import ResourceCreatedResponse


P = ParamSpec("P")


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


def pydantic_model_construct(cls: type[Model], **kwargs):
    import pydantic

    pydantic_version = int(pydantic.__version__[0])

    if pydantic_version < 2:
        return cls.construct(**kwargs)

    # Is it running in compatibility mode?
    if pydantic.v1.main.BaseModel in cls.__mro__:
        return cls.construct(**kwargs)

    return cls.model_construct(**kwargs)


def rewrap_in_class(cls: type[Model]):
    def decorator(func: Callable[P, ResourceCreatedResponse]):
        # This wrapper is used for asynchronous functions to ensure they are properly awaited and their results are processed by `cls.construct`.
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            return pydantic_model_construct(cls, **kwargs, **result.dict())

        # This wrapper handles synchronous functions, directly calling them and processing their results with `cls.construct`.
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Logging at this point might be useful for debugging, but should use a proper logging framework instead of print statements for production code.
            result = func(*args, **kwargs)
            return pydantic_model_construct(cls, **kwargs, **result.dict())

        return async_wrapper if iscoroutinefunction(func) else sync_wrapper

    return decorator
