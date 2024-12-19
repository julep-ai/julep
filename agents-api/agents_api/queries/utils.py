import concurrent.futures
import inspect
import random
import re
import socket
import time
from functools import partialmethod, wraps
from typing import (
    Any,
    Awaitable,
    Callable,
    Literal,
    NotRequired,
    ParamSpec,
    Type,
    TypeVar,
    cast,
)

import asyncpg
from asyncpg import Record
from beartype import beartype
from fastapi import HTTPException
from pydantic import BaseModel
from typing_extensions import TypedDict

from ..app import app
from ..env import query_timeout

P = ParamSpec("P")
T = TypeVar("T")
ModelT = TypeVar("ModelT", bound=BaseModel)


def generate_canonical_name(name: str) -> str:
    """Convert a display name to a canonical name.
    Example: "My Cool Agent!" -> "my_cool_agent"
    """
    # Remove special characters, replace spaces with underscores
    canonical = re.sub(r"[^\w\s-]", "", name.lower())
    canonical = re.sub(r"[-\s]+", "_", canonical)

    # Ensure it starts with a letter (prepend 'a' if not)
    if not canonical[0].isalpha():
        canonical = f"a_{canonical}"

    # Add 3 random numbers to the end
    canonical = f"{canonical}_{random.randint(100, 999)}"

    return canonical


def partialclass(cls, *args, **kwargs):
    cls_signature = inspect.signature(cls)
    bound = cls_signature.bind_partial(*args, **kwargs)

    # The `updated=()` argument is necessary to avoid a TypeError when using @wraps for a class
    @wraps(cls, updated=())
    class NewCls(cls):
        __init__ = partialmethod(cls.__init__, *bound.args, **bound.kwargs)

    return NewCls


class AsyncPGFetchArgs(TypedDict):
    query: str
    args: list[Any]
    timeout: NotRequired[float | None]


type SQLQuery = str
type FetchMethod = Literal["fetch", "fetchmany", "fetchrow"]
type PGQueryArgs = tuple[SQLQuery, list[Any]] | tuple[SQLQuery, list[Any], FetchMethod]
type PreparedPGQueryArgs = tuple[FetchMethod, AsyncPGFetchArgs]
type BatchedPreparedPGQueryArgs = list[PreparedPGQueryArgs]


@beartype
def prepare_pg_query_args(
    query_args: PGQueryArgs | list[PGQueryArgs],
) -> BatchedPreparedPGQueryArgs:
    batch = []
    query_args = [query_args] if isinstance(query_args, tuple) else query_args

    for query_arg in query_args:
        match query_arg:
            case (query, variables) | (query, variables, "fetch"):
                batch.append(
                    (
                        "fetch",
                        AsyncPGFetchArgs(
                            query=query, args=variables, timeout=query_timeout
                        ),
                    )
                )
            case (query, variables, "fetchmany"):
                batch.append(
                    (
                        "fetchmany",
                        AsyncPGFetchArgs(
                            query=query, args=[variables], timeout=query_timeout
                        ),
                    )
                )
            case (query, variables, "fetchrow"):
                batch.append(
                    (
                        "fetchrow",
                        AsyncPGFetchArgs(
                            query=query, args=variables, timeout=query_timeout
                        ),
                    )
                )
            case _:
                raise ValueError("Invalid query arguments")

    return batch


@beartype
def pg_query(
    func: Callable[P, PGQueryArgs | list[PGQueryArgs]] | None = None,
    debug: bool | None = None,
    only_on_error: bool = False,
    timeit: bool = False,
    return_index: int = -1,
) -> Callable[..., Callable[P, list[Record]]] | Callable[P, list[Record]]:
    def pg_query_dec(
        func: Callable[P, PGQueryArgs | list[PGQueryArgs]],
    ) -> Callable[..., Callable[P, list[Record]]]:
        """
        Decorator that wraps a function that takes arbitrary arguments, and
        returns a (query string, variables) tuple.

        The wrapped function should additionally take a client keyword argument
        and then run the query using the client, returning a Record.
        """

        from pprint import pprint

        @wraps(func)
        async def wrapper(
            *args: P.args,
            connection_pool: asyncpg.Pool | None = None,
            **kwargs: P.kwargs,
        ) -> list[Record]:
            query_args = await func(*args, **kwargs)
            batch = prepare_pg_query_args(query_args)

            not only_on_error and debug and pprint(batch)

            # Run the query
            pool = (
                connection_pool
                if connection_pool is not None
                else cast(asyncpg.Pool, app.state.postgres_pool)
            )

            try:
                async with pool.acquire() as conn:
                    async with conn.transaction():
                        start = timeit and time.perf_counter()
                        all_results = []
                        
                        for method_name, payload in batch:
                            method = getattr(conn, method_name)

                            query = payload["query"]
                            args = payload["args"]
                            timeout = payload.get("timeout")

                            results: list[Record] = await method(
                                query, *args, timeout=timeout
                            )
                            all_results.append(results)

                            if method_name == "fetchrow" and (
                                len(results) == 0 or results.get("bool") is None
                            ):
                                raise asyncpg.NoDataFoundError

                        end = timeit and time.perf_counter()

                        timeit and print(
                            f"PostgreSQL query time: {end - start:.2f} seconds"
                        )

            except Exception as e:
                if only_on_error and debug:
                    pprint(batch)

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

            # Return results from specified index
            results_to_return = all_results[return_index] if all_results else []
            not only_on_error and debug and pprint(results_to_return)
            
            return results_to_return

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
) -> Callable[..., Callable[..., ModelT | list[ModelT]]]:
    def _return_data(rec: list[Record]):
        data = [dict(r.items()) for r in rec]

        nonlocal transform
        transform = transform or (lambda x: x)

        if one:
            assert len(data) == 1, "Expected one result, got none"
            obj: ModelT = cls(**transform(data[0]))
            return obj

        objs: list[ModelT] = [cls(**item) for item in map(transform, data)]
        return objs

    def decorator(
        func: Callable[P, list[Record] | Awaitable[list[Record]]],
    ) -> Callable[P, ModelT | list[ModelT]]:
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
) -> Callable[..., Callable[P, T | Awaitable[T]]]:
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

    def decorator(
        func: Callable[P, T | Awaitable[T]],
    ) -> Callable[..., Callable[P, T | Awaitable[T]]]:
        @wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                result: T = await func(*args, **kwargs)
            except BaseException as error:
                _check_error(error)
                raise error

            return result

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                result: T = func(*args, **kwargs)
            except BaseException as error:
                _check_error(error)
                raise error

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
