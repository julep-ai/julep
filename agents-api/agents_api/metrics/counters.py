import inspect
from functools import wraps
from typing import Awaitable, Callable, ParamSpec, TypeVar

from prometheus_client import Counter

P = ParamSpec("P")
T = TypeVar("T")


def increase_counter(metric_label: str, id_field_name: str = "developer_id"):
    def decor(func: Callable[P, T | Awaitable[T]]):
        metric = Counter(
            metric_label,
            f"Number of {metric_label} calls",
            labelnames=(id_field_name,),
        )

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            metric.labels(kwargs.get(id_field_name, "not_set")).inc()
            return func(*args, **kwargs)

        @wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            metric.labels(kwargs.get(id_field_name, "not_set")).inc()
            return func(*args, **kwargs)

        return async_wrapper if inspect.iscoroutinefunction(func) else wrapper

    return decor
