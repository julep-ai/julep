import inspect
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import ParamSpec, TypeVar

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
            return await func(*args, **kwargs)

        return async_wrapper if inspect.iscoroutinefunction(func) else wrapper

    return decor


# FIXME: Find out why the following code is not working

# import inspect
# import time
# from collections.abc import Awaitable, Callable
# from functools import wraps
# from typing import ParamSpec, TypeVar

# from prometheus_client import Counter, Histogram, Summary
# from prometheus_client.utils import INF

# P = ParamSpec("P")
# T = TypeVar("T")


# id_field_name = "developer_id"
# labelnames = ("developer_id", "query_name")
# buckets = (
#     0.005,
#     0.01,
#     0.025,
#     0.05,
#     0.075,
#     0.1,
#     0.25,
#     0.5,
#     0.75,
#     1.0,
#     2.5,
#     5.0,
#     7.5,
#     10.0,
#     15.0,
#     20.0,
#     25.0,
#     30.0,
#     INF,
# )
# counter = Counter(
#     "db_query_counter",
#     "Number of db calls",
#     labelnames=labelnames,
# )
# summary = Summary(
#     "db_query_latency_summary",
#     "Database query latency summary",
#     labelnames=labelnames,
# )
# hist = Histogram(
#     "db_query_latency_hist",
#     "Database query latency histogram",
#     labelnames=labelnames,
#     buckets=buckets,
# )


# def query_metrics_update(metric_label: str):
#     def decor(func: Callable[P, T | Awaitable[T]]):
#         if inspect.iscoroutinefunction(func):

#             @wraps(func)
#             async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
#                 fld_id = kwargs.get(id_field_name, "not_set")
#                 labels_dict = {id_field_name: fld_id, "query_name": metric_label}
#                 counter.labels(**labels_dict).inc()
#                 start_time = time.time()
#                 result = await func(*args, **kwargs)
#                 end_time = time.time() - start_time
#                 summary.labels(**labels_dict).observe(end_time)
#                 hist.labels(**labels_dict).observe(end_time)
#                 return result

#             return async_wrapper

#         @wraps(func)
#         def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
#             fld_id = kwargs.get(id_field_name, "not_set")
#             labels_dict = {id_field_name: fld_id, "query_name": metric_label}
#             counter.labels(**labels_dict).inc()
#             start_time = time.time()
#             result = func(*args, **kwargs)
#             end_time = time.time() - start_time
#             summary.labels(**labels_dict).observe(end_time)
#             hist.labels(**labels_dict).observe(end_time)
#             return result

#         return wrapper

#     return decor
