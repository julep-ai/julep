import psutil
from starlette_exporter import PrometheusMiddleware
from prometheus_client import Gauge, Counter
from pynvml import *


nvmlInit()


def _gpu_usage():
    res = []
    for index in range(nvmlDeviceGetCount()):
        handle = nvmlDeviceGetHandleByIndex(index)
        info = nvmlDeviceGetMemoryInfo(handle)
        try:
            util = nvmlDeviceGetUtilizationRates(handle)
            util_gpu = util.gpu
            util_memory = util.memory
        except:
            util_gpu = 0
            util_memory = 0

        res.append(
            {
                "mem_total": info.total,
                "mem_free": info.free,
                "mem_used": info.used,
                "gpu_util_percents": util_gpu,
                "gpu_memory_percents": util_memory,
            }
        )

    return res


cpu_percent_metric = Gauge(
    "cpu_percent_usage_info",
    "CPU percent usage info",
)
mem_total_metric = Gauge(
    "mem_total_info",
    "Total memory info",
)
mem_free_metric = Gauge(
    "mem_free_info",
    "Free memory info",
)
mem_used_metric = Gauge(
    "mem_used_info",
    "Used memory info",
)
mem_percent_metric = Gauge(
    "mem_percent_info",
    "Memory used percentage info",
)


gpu_mem_total_metric = Gauge(
    "gpu_mem_total",
    "GPU memory total",
    labelnames=("gpu_index",),
)
gpu_mem_free_metric = Gauge(
    "gpu_mem_free",
    "GPU memory free",
    labelnames=("gpu_index",),
)
gpu_mem_used_metric = Gauge(
    "gpu_mem_used",
    "GPU memory used",
    labelnames=("gpu_index",),
)
gpu_util_percents_metric = Gauge(
    "gpu_util_percents",
    "GPU utilization percents",
    labelnames=("gpu_index",),
)
gpu_memory_percents_metric = Gauge(
    "gpu_memory_percents",
    "GPU utilization percents",
    labelnames=("gpu_index",),
)


tokens_per_user_metric = Counter(
    "total_tokens_per_user",
    "Total tokens per user",
    labelnames=("user_name", "user_email"),
)


generation_time_metric = Gauge(
    "model_response_generation_time",
    "Model response generation time",
    labelnames=("user_name", "user_email"),
)


generated_tokens_per_second_metric = Gauge(
    "generated_token_per_second",
    "Generated tokens per second",
    labelnames=("user_name", "user_email"),
)


class MetricsMiddleware(PrometheusMiddleware):
    async def __call__(self, *args, **kwargs):
        mem = psutil.virtual_memory()
        cpu_percent_metric.set(psutil.cpu_percent())
        mem_total_metric.set(mem.total)
        mem_free_metric.set(mem.free)
        mem_used_metric.set(mem.used)
        mem_percent_metric.set(mem.percent)

        usage = _gpu_usage()
        for idx, u in enumerate(usage):
            idx = str(idx)
            gpu_mem_total_metric.labels(idx).set(u["mem_total"])
            gpu_mem_free_metric.labels(idx).set(u["mem_free"])
            gpu_mem_used_metric.labels(idx).set(u["mem_used"])
            gpu_util_percents_metric.labels(idx).set(u["gpu_util_percents"])
            gpu_memory_percents_metric.labels(idx).set(u["gpu_memory_percents"])

        return await super().__call__(*args, **kwargs)
