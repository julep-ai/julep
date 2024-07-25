from functools import wraps
from typing import Callable, ParamSpec, Type
from uuid import UUID

from beartype import beartype
from pydantic import BaseModel
import pandas as pd

from ..clients.cozo import client as cozo_client


P = ParamSpec("P")


def verify_developer_id_query(developer_id: UUID | str) -> str:
    return f"""
    ?[developer_id] :=
        *developers{{
            developer_id,
        }}, developer_id = to_uuid("{str(developer_id)}")
        
    :assert some
    """


def verify_developer_owns_resource_query(
    developer_id: UUID | str, resource: str, **resource_id: dict
) -> str:

    resource_id_key, resource_id_value = next(iter(resource_id.items()))

    return f"""
    ?[{resource_id_key}] :=
        *{resource}{{
            developer_id,
            {resource_id_key},
        }}, developer_id = to_uuid("{str(developer_id)}"),
        {resource_id_key} = to_uuid("{str(resource_id_value)}")
        
    :assert some
    """


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
