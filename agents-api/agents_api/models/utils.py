from functools import wraps
from typing import Callable, ParamSpec

import pandas as pd

from ..clients.cozo import client as cozo_client


P = ParamSpec("P")


def cozo_query(func: Callable[P, tuple[str, dict]]):
    """
    Decorator that wraps a function that takes arbitrary arguments, and
    returns a (query string, variables) tuple.

    The wrapped function should additionally take a client keyword argument
    and then run the query using the client, returning a DataFrame.
    """

    @wraps(func)
    def wrapper(*args, client=cozo_client, **kwargs) -> pd.DataFrame:
        query, variables = func(*args, **kwargs)
        return client.run(query, variables)

    return wrapper
