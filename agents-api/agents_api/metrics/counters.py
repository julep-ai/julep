import inspect
from functools import wraps
from typing import Awaitable, Callable, ParamSpec, TypeVar

from prometheus_client import Counter, Summary

P = ParamSpec("P")
T = TypeVar("T")


def query_metrics_update(metric_label: str, id_field_name: str = "developer_id"):
    def decor(func: Callable[P, T | Awaitable[T]]):
        counter = Counter(
            f"cozo_counter_{metric_label}",
            f"Number of {metric_label} calls",
            labelnames=(id_field_name,),
        )
        summary = Summary(
            f"cozo_latency_{metric_label}",
            metric_label,
        )

        @summary.time()
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            counter.labels(kwargs.get(id_field_name, "not_set")).inc()
            return func(*args, **kwargs)

        @summary.time()
        @wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            counter.labels(kwargs.get(id_field_name, "not_set")).inc()
            return await func(*args, **kwargs)

        return async_wrapper if inspect.iscoroutinefunction(func) else wrapper

    return decor
