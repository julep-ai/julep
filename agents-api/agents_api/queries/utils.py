import concurrent.futures
import inspect
import socket
import time
from functools import partialmethod, wraps
from typing import Any, Awaitable, Callable, ParamSpec, Type, TypeVar

import pandas as pd
from asyncpg import Record
from fastapi import HTTPException
from pydantic import BaseModel

P = ParamSpec("P")
T = TypeVar("T")
ModelT = TypeVar("ModelT", bound=BaseModel)


def partialclass(cls, *args, **kwargs):
    cls_signature = inspect.signature(cls)
    bound = cls_signature.bind_partial(*args, **kwargs)

    # The `updated=()` argument is necessary to avoid a TypeError when using @wraps for a class
    @wraps(cls, updated=())
    class NewCls(cls):
        __init__ = partialmethod(cls.__init__, *bound.args, **bound.kwargs)

    return NewCls


def pg_query(
    func: Callable[P, tuple[str | list[str | None], dict]] | None = None,
    debug: bool | None = None,
    only_on_error: bool = False,
    timeit: bool = False,
):
    def pg_query_dec(func: Callable[P, tuple[str | list[Any], dict]]):
        """
        Decorator that wraps a function that takes arbitrary arguments, and
        returns a (query string, variables) tuple.

        The wrapped function should additionally take a client keyword argument
        and then run the query using the client, returning a Record.
        """

        from pprint import pprint

        from tenacity import (
            retry,
            retry_if_exception,
            stop_after_attempt,
            wait_exponential,
        )
        
        # TODO: Remove all tenacity decorators
        # @retry(
        #     stop=stop_after_attempt(4),
        #     wait=wait_exponential(multiplier=1, min=4, max=10),
        #     # retry=retry_if_exception(is_resource_busy),
        # )
        @wraps(func)
        async def wrapper(
            *args: P.args, client=None, **kwargs: P.kwargs
        ) -> list[Record]:
            query, variables = await func(*args, **kwargs)

            not only_on_error and debug and print(query)
            not only_on_error and debug and pprint(
                dict(
                    variables=variables,
                )
            )

            # Run the query
            from ..clients import pg

            try:
                client = client or await pg.get_pg_client()

                start = timeit and time.perf_counter()
                results: list[Record] = await client.fetch(query, *variables)
                end = timeit and time.perf_counter()

                timeit and print(f"PostgreSQL query time: {end - start:.2f} seconds")

            except Exception as e:
                if only_on_error and debug:
                    print(query)
                    pprint(variables)

                debug and print(repr(e))
                connection_error = isinstance(
                    e,
                    (socket.gaierror),
                )

                if connection_error:
                    exc = HTTPException(
                        status_code=429, detail="Resource busy. Please try again later."
                    )
                    raise exc from e

                raise

            not only_on_error and debug and pprint(
                dict(
                    results=[dict(result.items()) for result in results],
                )
            )

            return results

        # Set the wrapped function as an attribute of the wrapper,
        # forwards the __wrapped__ attribute if it exists.
        setattr(wrapper, "__wrapped__", getattr(func, "__wrapped__", func))

        return wrapper

    if func is not None and callable(func):
        return pg_query_dec(func)

    return pg_query_dec


def wrap_in_class(
    cls: Type[ModelT] | Callable[..., ModelT],
    one: bool = False,
    transform: Callable[[dict], dict] | None = None,
    _kind: str | None = None,
):
    def _return_data(rec: list[Record]):
        # Convert df to list of dicts
        # if _kind:
        #     rec = rec[rec["_kind"] == _kind]

        data = [dict(r.items()) for r in rec]

        nonlocal transform
        transform = transform or (lambda x: x)

        if one:
            assert len(data) >= 1, "Expected one result, got none"
            obj: ModelT = cls(**transform(data[0]))
            return obj

        objs: list[ModelT] = [cls(**item) for item in map(transform, data)]
        return objs

    def decorator(func: Callable[P, pd.DataFrame | Awaitable[pd.DataFrame]]):
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> ModelT | list[ModelT]:
            return _return_data(func(*args, **kwargs))

        @wraps(func)
        async def async_wrapper(
            *args: P.args, **kwargs: P.kwargs
        ) -> ModelT | list[ModelT]:
            return _return_data(await func(*args, **kwargs))

        # Set the wrapped function as an attribute of the wrapper,
        # forwards the __wrapped__ attribute if it exists.
        setattr(wrapper, "__wrapped__", getattr(func, "__wrapped__", func))
        setattr(async_wrapper, "__wrapped__", getattr(func, "__wrapped__", func))

        return async_wrapper if inspect.iscoroutinefunction(func) else wrapper

    return decorator


def rewrap_exceptions(
    mapping: dict[
        Type[BaseException] | Callable[[BaseException], bool],
        Type[BaseException] | Callable[[BaseException], BaseException],
    ],
    /,
):
    def _check_error(error):
        nonlocal mapping

        for check, transform in mapping.items():
            should_catch = (
                isinstance(error, check) if isinstance(check, type) else check(error)
            )

            if should_catch:
                new_error = (
                    transform(str(error))
                    if isinstance(transform, type)
                    else transform(error)
                )

                setattr(new_error, "__cause__", error)

                raise new_error from error

    def decorator(func: Callable[P, T | Awaitable[T]]):
        @wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                result: T = await func(*args, **kwargs)
            except BaseException as error:
                _check_error(error)
                raise

            return result

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                result: T = func(*args, **kwargs)
            except BaseException as error:
                _check_error(error)
                raise

            return result

        # Set the wrapped function as an attribute of the wrapper,
        # forwards the __wrapped__ attribute if it exists.
        setattr(wrapper, "__wrapped__", getattr(func, "__wrapped__", func))
        setattr(async_wrapper, "__wrapped__", getattr(func, "__wrapped__", func))

        return async_wrapper if inspect.iscoroutinefunction(func) else wrapper

    return decorator


def run_concurrently(
    fns: list[Callable[..., Any]],
    *,
    args_list: list[tuple] = [],
    kwargs_list: list[dict] = [],
) -> list[Any]:
    args_list = args_list or [tuple()] * len(fns)
    kwargs_list = kwargs_list or [dict()] * len(fns)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(fn, *args, **kwargs)
            for fn, args, kwargs in zip(fns, args_list, kwargs_list)
        ]

        return [future.result() for future in concurrent.futures.as_completed(futures)]
