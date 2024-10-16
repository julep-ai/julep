import inspect
import sys
from functools import wraps
from typing import Any, Callable

from ..clients import s3
from ..common.protocol.tasks import RemoteObject
from ..env import blob_store_cutoff_kb, use_blob_store_for_temporal
from ..worker.codec import deserialize, serialize

if use_blob_store_for_temporal:
    s3.setup()


def store_in_blob_store_if_large(x: Any) -> RemoteObject | Any:
    serialized = serialize(x)
    data_size = sys.getsizeof(serialized)

    if data_size > blob_store_cutoff_kb * 1024:
        key = s3.add_object_with_hash(serialized)
        return RemoteObject(key=key)

    return x


def load_from_blob_store_if_remote(x: Any) -> Any:
    if isinstance(x, RemoteObject):
        fetched = s3.get_object(x.key)
        return deserialize(fetched)

    return x


# Decorator that automatically does two things:
# 1. store in blob store if the output of a function is large
# 2. load from blob store if the input is a RemoteObject


def auto_blob_store(f: Callable) -> Callable:
    def load_args(
        args: list[Any], kwargs: dict[str, Any]
    ) -> tuple[list[Any], dict[str, Any]]:
        new_args = [load_from_blob_store_if_remote(arg) for arg in args]
        new_kwargs = {k: load_from_blob_store_if_remote(v) for k, v in kwargs.items()}

        return new_args, new_kwargs

    if inspect.iscoroutinefunction(f):

        @wraps(f)
        async def async_wrapper(*args, **kwargs) -> Any:
            new_args, new_kwargs = load_args(args, kwargs)
            output = await f(*new_args, **new_kwargs)

            return store_in_blob_store_if_large(output)

        return async_wrapper if use_blob_store_for_temporal else f

    else:

        @wraps(f)
        def wrapper(*args, **kwargs) -> Any:
            new_args, new_kwargs = load_args(args, kwargs)
            output = f(*new_args, **new_kwargs)

            return store_in_blob_store_if_large(output)

        return wrapper if use_blob_store_for_temporal else f
