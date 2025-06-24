# AIDEV-NOTE: This module contains utility functions and decorators for database queries and data processing.
import concurrent.futures
import inspect
import socket
import time
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import (
    Any,
    Literal,
    NotRequired,
    ParamSpec,
    TypeVar,
    cast,
)

import asyncpg
import namer
from asyncpg import Record
from beartype import beartype
from fastapi import HTTPException
from pydantic import BaseModel
from typing_extensions import TypedDict

from agents_api.common.exceptions.validation import QueryParamsValidationError

from ..app import app
from ..env import query_timeout

P = ParamSpec("P")
T = TypeVar("T")
ModelT = TypeVar("ModelT", bound=BaseModel)


# AIDEV-NOTE: Generates a unique, readable canonical name.
def generate_canonical_name() -> str:
    """Generate canonical name"""

    categories: list[str] = ["astronomy", "physics", "scientists", "math"]
    return namer.generate(separator="_", suffix_length=3, category=categories)


class AsyncPGFetchArgs(TypedDict):
    query: str
    args: list[Any]
    timeout: NotRequired[float | None]


type SQLQuery = str
type FetchMethod = Literal["fetch", "fetchmany", "fetchrow"]
type PGQueryArgs = tuple[SQLQuery, list[Any]] | tuple[SQLQuery, list[Any], FetchMethod]
type PreparedPGQueryArgs = tuple[FetchMethod, AsyncPGFetchArgs]
type BatchedPreparedPGQueryArgs = list[PreparedPGQueryArgs]


# AIDEV-NOTE: Prepares and formats PostgreSQL query arguments for batch execution.
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
                msg = "Invalid query arguments"
                raise ValueError(msg)

    return batch


# AIDEV-NOTE: Decorator for executing PostgreSQL queries within a transaction.
# Handles connection pooling, error handling, and result formatting.
@beartype
def pg_query[**P](
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
                else cast(asyncpg.Pool, getattr(app.state, "postgres_pool", None))
            )

            try:
                async with pool.acquire() as conn, conn.transaction():
                    start = timeit and time.perf_counter()
                    all_results = []

                    for method_name, payload in batch:
                        method = getattr(conn, method_name)
                        query = payload["query"]
                        args = sanitize_string(payload["args"])
                        timeout = payload.get("timeout")
                        results: list[Record] = await method(
                            query, *args, timeout=timeout
                        )
                        if method_name == "fetchrow":
                            results = (
                                [results]
                                if results is not None
                                and results.get("bool", False) is not None
                                and results.get("exists", True)
                                else []
                            )

                        if method_name == "fetchrow" and len(results) == 0:
                            msg = "No data found"
                            raise asyncpg.NoDataFoundError(msg)

                        all_results.append(results)

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
                        status_code=429,
                        detail="Resource busy. Please try again later.",
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


# AIDEV-NOTE: Sanitizes strings to remove null characters for PostgreSQL compatibility.
def sanitize_string(value: Any) -> Any:
    """
    Remove null characters (\u0000) from strings for PostgreSQL compatibility.

    Args:
        value: Any data structure that might contain strings with null characters

    Returns:
        Data with null characters removed from strings
    """
    if isinstance(value, str):
        return value.replace("\u0000", "")
    if isinstance(value, dict):
        return {key: sanitize_string(val) for key, val in value.items()}
    if isinstance(value, list):
        return [sanitize_string(item) for item in value]
    if isinstance(value, tuple):
        return tuple(sanitize_string(item) for item in value)
    return value


# AIDEV-NOTE: Decorator to wrap query results in Pydantic models.
def wrap_in_class(
    cls: type[ModelT] | Callable[..., ModelT],
    one: bool = False,
    maybe_one: bool = False,
    transform: Callable[[dict], dict] | None = None,
) -> Callable[..., Callable[..., ModelT | list[ModelT] | None]]:
    """
    Decorator that wraps database query results into Pydantic model instances.

    Args:
        cls: The Pydantic model class or callable that constructs the model
        one: If True, expects exactly one result and returns a single model instance
        maybe_one: If True, returns None if no results, a single model if one result,
                  and raises ValueError if multiple results
        transform: Optional function to transform each record before model instantiation

    Returns:
        A decorator that transforms query results into model instances

    Raises:
        ValueError: If one=True and not exactly one result is returned, or
                   if maybe_one=True and multiple results are returned
    """

    def _return_data(rec: list[Record]) -> ModelT | list[ModelT] | None:
        data = [dict(r.items()) for r in rec]
        # AIDEV-NOTE: initialize transformer function once per call
        transform_fn = transform or (lambda x: x)

        if maybe_one:
            if len(data) == 0:
                return None
            if len(data) == 1:
                return cls(**transform_fn(data[0]))
            msg = f"Expected one result or none, got {len(data)}"
            raise ValueError(msg)

        if one:
            assert len(data) == 1, f"Expected one result, got {len(data)}"
            obj: ModelT = cls(**transform_fn(data[0]))
            return obj

        objs: list[ModelT] = [cls(**item) for item in map(transform_fn, data)]
        return objs

    def decorator(
        func: Callable[P, list[Record] | Awaitable[list[Record]]],
    ) -> Callable[P, ModelT | list[ModelT] | None]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> ModelT | list[ModelT] | None:
            return _return_data(func(*args, **kwargs))

        @wraps(func)
        async def async_wrapper(
            *args: P.args, **kwargs: P.kwargs
        ) -> ModelT | list[ModelT] | None:
            return _return_data(await func(*args, **kwargs))

        # Set the wrapped function as an attribute of the wrapper,
        # forwards the __wrapped__ attribute if it exists.
        setattr(wrapper, "__wrapped__", getattr(func, "__wrapped__", func))
        setattr(async_wrapper, "__wrapped__", getattr(func, "__wrapped__", func))

        return async_wrapper if inspect.iscoroutinefunction(func) else wrapper

    return decorator


# AIDEV-NOTE: Decorator to rewrap specific exceptions raised by a function.
def rewrap_exceptions(
    mapping: dict[
        type[BaseException] | Callable[[BaseException], bool],
        type[BaseException] | Callable[[BaseException], BaseException],
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

                print(error)
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


# AIDEV-NOTE: Runs multiple asynchronous functions concurrently.
def run_concurrently(
    fns: list[Callable[..., Any]],
    *,
    args_list: list[tuple] | None = None,
    kwargs_list: list[dict] | None = None,
) -> list[Any]:
    # AIDEV-NOTE: avoid mutable default args; initialize to empty list if None
    args_list = args_list if args_list is not None else []
    kwargs_list = kwargs_list if kwargs_list is not None else []
    args_list = args_list or [()] * len(fns)
    kwargs_list = kwargs_list or [{}] * len(fns)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(fn, *args, **kwargs)
            for fn, args, kwargs in zip(fns, args_list, kwargs_list)
        ]

        return [future.result() for future in concurrent.futures.as_completed(futures)]


# AIDEV-NOTE: Serializes Pydantic model data into a dictionary, handling nested models.
def serialize_model_data(data: Any) -> Any:
    """
    Recursively serialize Pydantic models and their nested structures.

    Args:
        data: Any data structure that might contain Pydantic models

    Returns:
        JSON-serializable data structure
    """
    if hasattr(data, "model_dump"):
        return data.model_dump(mode="json")
    if isinstance(data, dict):
        return {key: serialize_model_data(value) for key, value in data.items()}
    if isinstance(data, list | tuple):
        return [serialize_model_data(item) for item in data]
    return data


# AIDEV-NOTE: Builds SQL conditions for filtering based on JSONB metadata.
def build_metadata_filter_conditions(
    base_params: list[Any], metadata_filter: dict[str, Any], table_alias: str = ""
) -> tuple[str, list[Any]]:
    """
    Safely build SQL conditions for metadata filtering to prevent SQL injection.

    This function takes a base parameter list and a metadata filter dictionary, and returns
    a tuple containing the SQL conditions string and an updated parameter list with the
    metadata filter values appended.

    Args:
        base_params: The existing list of parameters for the SQL query
        metadata_filter: A dictionary of key-value pairs to filter by metadata
        table_alias: Optional table alias (e.g., "d.") to prefix to metadata column name

    Returns:
        tuple[str, list[Any]]: A tuple containing the SQL condition string and the updated parameter list
    """
    if not metadata_filter:
        return "", base_params

    params = base_params.copy()
    conditions = []
    metadata_col = f"{table_alias}metadata" if table_alias else "metadata"

    for key, value in metadata_filter.items():
        param_idx_key = len(params) + 1
        param_idx_value = len(params) + 2
        conditions.append(f"{metadata_col}->>${param_idx_key} = ${param_idx_value}")
        params.extend([key, value])

    sql_conditions = " AND ".join(conditions)
    if sql_conditions:
        sql_conditions = " AND " + sql_conditions

    return sql_conditions, params


# AIDEV-NOTE: Creates a validator function for numerical ranges.
def make_num_validator(
    min_value: int | float | None = None,
    max_value: int | float | None = None,
    err_msg: str | None = None,
):
    def validator(v: int | float) -> bool:
        # Choose appropriate error message without mutating outer err_msg
        if min_value is not None and v < min_value:
            msg = err_msg or f"Number must be greater than or equal to {min_value}"
            raise QueryParamsValidationError(msg)

        if max_value is not None and v > max_value:
            msg = err_msg or f"Number must be less than or equal to {max_value}"
            raise QueryParamsValidationError(msg)

        return True

    return validator
