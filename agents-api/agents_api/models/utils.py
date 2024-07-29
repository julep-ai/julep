import inspect
from functools import partialmethod, wraps
from typing import Any, Callable, ParamSpec, Type
from uuid import UUID

import pandas as pd
from pydantic import BaseModel

from ..clients.cozo import client as cozo_client

P = ParamSpec("P")


def partialclass(cls, *args, **kwargs):
    cls_signature = inspect.signature(cls)
    bound = cls_signature.bind_partial(*args, **kwargs)

    # The `updated=()` argument is necessary to avoid a TypeError when using @wraps for a class
    @wraps(cls, updated=())
    class NewCls(cls):
        __init__ = partialmethod(cls.__init__, *bound.args, **bound.kwargs)

    return NewCls


def verify_developer_id_query(developer_id: UUID | str) -> str:
    return f"""
    ?[developer_id] :=
        *developers{{
            developer_id,
        }}, developer_id = to_uuid("{str(developer_id)}")
        
    :assert some
    """


def verify_developer_owns_resource_query(
    developer_id: UUID | str,
    resource: str,
    parents: list[tuple[str, str]] | None = None,
    **resource_id,
) -> str:
    parents = parents or []
    resource_id_key, resource_id_value = next(iter(resource_id.items()))

    parents.append((resource, resource_id_key))
    parent_keys = ["developer_id", *map(lambda x: x[1], parents)]

    rule_head = f"""
    ?[{resource_id_key}] :=
        developer_id = to_uuid("{str(developer_id)}"),
        {resource_id_key} = to_uuid("{str(resource_id_value)}"),
    """

    rule_body = ""
    for parent_key, (relation, key) in zip(parent_keys, parents):
        rule_body += f"""
        *{relation}{{
            {parent_key},
            {key},
        }},
        """

    rule = rule_head + rule_body + "\n:assert some"
    return rule


def cozo_query(
    func: Callable[P, tuple[str, dict]] | None = None, debug: bool | None = None
):
    def cozo_query_dec(func: Callable[P, tuple[str, dict]]):
        """
        Decorator that wraps a function that takes arbitrary arguments, and
        returns a (query string, variables) tuple.

        The wrapped function should additionally take a client keyword argument
        and then run the query using the client, returning a DataFrame.
        """

        if debug:
            from pprint import pprint

        @wraps(func)
        def wrapper(*args, client=cozo_client, **kwargs) -> pd.DataFrame:
            query, variables = func(*args, **kwargs)

            debug and pprint(
                dict(
                    query=query,
                    variables=variables,
                )
            )

            result = client.run(query, variables)

            debug and pprint(
                dict(
                    result=result.to_dict(orient="records"),
                )
            )

            return result

        # Set the wrapped function as an attribute of the wrapper,
        # forwards the __wrapped__ attribute if it exists.
        setattr(wrapper, "__wrapped__", getattr(func, "__wrapped__", func))

        return wrapper

    if func is not None and callable(func):
        return cozo_query_dec(func)

    return cozo_query_dec


def wrap_in_class(
    cls: Type[BaseModel] | Callable[..., BaseModel],
    one: bool = False,
    transform: Callable[[dict], dict] | None = None,
):
    def decorator(func: Callable[..., pd.DataFrame]):
        @wraps(func)
        def wrapper(*args, **kwargs):
            df = func(*args, **kwargs)

            # Convert df to list of dicts
            data = df.to_dict(orient="records")

            nonlocal transform
            transform = transform or (lambda x: x)
            if one:
                return cls(**transform(data[0]))

            return [cls(**item) for item in map(transform, data)]

        # Set the wrapped function as an attribute of the wrapper,
        # forwards the __wrapped__ attribute if it exists.
        setattr(wrapper, "__wrapped__", getattr(func, "__wrapped__", func))

        return wrapper

    return decorator


def rewrap_exceptions(
    mapping: dict[
        Type[BaseException] | Callable[[BaseException], bool],
        Type[BaseException] | Callable[[BaseException], BaseException],
    ],
    /,
):
    def decorator(func: Callable[..., Any]):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal mapping

            try:
                result = func(*args, **kwargs)

            except BaseException as error:
                for check, transform in mapping.items():
                    should_catch = (
                        isinstance(error, check)
                        if isinstance(check, type)
                        else check(error)
                    )

                    if should_catch:
                        new_error = (
                            transform(str(error))
                            if isinstance(transform, type)
                            else transform(error)
                        )

                        raise transform(error) from error

                raise

            return result

        # Set the wrapped function as an attribute of the wrapper,
        # forwards the __wrapped__ attribute if it exists.
        setattr(wrapper, "__wrapped__", getattr(func, "__wrapped__", func))

        return wrapper

    return decorator
