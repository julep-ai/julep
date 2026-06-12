from __future__ import annotations

import json
import statistics
import sys
import time
from importlib import metadata
from pathlib import Path
from typing import Any, Callable

from wasmtime import Config, Engine, Store, WasiConfig, WasmtimeError
from wasmtime.component import Component, Linker

from build import COMPILED, COMPONENT, ensure_built

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results.json"
CALLS = 120
WARMUP_CALLS = 5


REALISTIC_SOURCE = """
def transform(value, *, multiplier=3, label="score"):
    rows = []
    total = 0
    for item in value["items"]:
        adjusted = (item["score"] + value.get("offset", 0)) * multiplier
        total += adjusted
        rows.append({
            "id": item["id"],
            "bucket": "high" if adjusted >= 20 else "low",
            label: adjusted,
        })
    return {"rows": rows, "total": total, "count": len(rows)}
"""

REALISTIC_VALUE = {
    "offset": 2,
    "items": [
        {"id": "a", "score": 2},
        {"id": "b", "score": 7},
        {"id": "c", "score": 11},
        {"id": "d", "score": 1},
        {"id": "e", "score": 9},
    ],
}


def make_engine() -> Engine:
    config = Config()
    config.wasm_component_model = True
    return Engine(config)


ENGINE = make_engine()
LINKER = Linker(ENGINE)
LINKER.add_wasip2()


def make_store() -> Store:
    store = Store(ENGINE)
    wasi = WasiConfig()
    wasi.inherit_stdout()
    wasi.inherit_stderr()
    store.set_wasi(wasi)
    return store


def instantiate(component: Component) -> tuple[Store, Any]:
    store = make_store()
    instance = LINKER.instantiate(store, component)
    run = instance.get_func(store, "run")
    if run is None:
        raise RuntimeError("component export 'run' not found")
    return store, run


def instantiate_bare(component: Component) -> tuple[Store, Any]:
    store = Store(ENGINE)
    linker = Linker(ENGINE)
    instance = linker.instantiate(store, component)
    run = instance.get_func(store, "run")
    if run is None:
        raise RuntimeError("component export 'run' not found")
    return store, run


def call_run(run: Any, store: Store, request: dict[str, Any]) -> dict[str, Any]:
    raw = run(store, json.dumps(request, sort_keys=True, separators=(",", ":")))
    run.post_return(store)
    return json.loads(raw)


def call_with_deserialize(request: dict[str, Any]) -> dict[str, Any]:
    component = Component.deserialize_file(ENGINE, str(COMPILED))
    store, run = instantiate(component)
    return call_run(run, store, request)


def call_with_warm_component(component: Component, request: dict[str, Any]) -> dict[str, Any]:
    store, run = instantiate(component)
    return call_run(run, store, request)


def call_with_bare_linker(component: Component, request: dict[str, Any]) -> dict[str, Any]:
    store, run = instantiate_bare(component)
    return call_run(run, store, request)


def timed_call(func: Callable[[], dict[str, Any]]) -> tuple[float, dict[str, Any]]:
    start = time.perf_counter_ns()
    result = func()
    elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000
    return elapsed_ms, result


def percentile(values: list[float], percent: float) -> float:
    ordered = sorted(values)
    index = int((len(ordered) - 1) * percent)
    return ordered[index]


def summarize(samples: list[float]) -> dict[str, float]:
    return {
        "calls": len(samples),
        "median_ms": statistics.median(samples),
        "p95_ms": percentile(samples, 0.95),
        "min_ms": min(samples),
        "max_ms": max(samples),
    }


def request(source: str, func: str, value: Any, static_args: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "source": source,
        "func": func,
        "value": value,
        "static_args": static_args or {},
    }


def benchmark(
    name: str,
    invoke: Callable[[dict[str, Any]], dict[str, Any]],
) -> dict[str, Any]:
    payload = request(
        REALISTIC_SOURCE,
        "transform",
        REALISTIC_VALUE,
        {"multiplier": 4, "label": "weighted"},
    )
    for _ in range(WARMUP_CALLS):
        result = invoke(payload)
        assert result["ok"], result

    samples = []
    for _ in range(CALLS):
        elapsed, result = timed_call(lambda: invoke(payload))
        assert result["ok"], result
        samples.append(elapsed)
    return {"name": name, **summarize(samples)}


def instantiate_execute(component: Component, payload: dict[str, Any]) -> dict[str, Any]:
    store, run = instantiate(component)
    return call_run(run, store, payload)


def breakdown(component: Component) -> dict[str, Any]:
    payload = request(
        REALISTIC_SOURCE,
        "transform",
        REALISTIC_VALUE,
        {"multiplier": 4, "label": "weighted"},
    )
    deserialize_samples: list[float] = []
    instantiate_execute_samples: list[float] = []
    execute_existing_instance_samples: list[float] = []

    store, run = instantiate(component)
    for _ in range(CALLS):
        start = time.perf_counter_ns()
        Component.deserialize_file(ENGINE, str(COMPILED))
        deserialize_samples.append((time.perf_counter_ns() - start) / 1_000_000)

        elapsed, result = timed_call(lambda: instantiate_execute(component, payload))
        assert result["ok"], result
        instantiate_execute_samples.append(elapsed)

        elapsed, result = timed_call(
            lambda: call_run(run, store, payload)
        )
        assert result["ok"], result
        execute_existing_instance_samples.append(elapsed)

    return {
        "deserialize_file": summarize(deserialize_samples),
        "instantiate_fresh_store_and_execute": summarize(instantiate_execute_samples),
        "execute_existing_instance_only_not_fresh": summarize(execute_existing_instance_samples),
    }


def run_probe(
    component: Component,
    source: str,
    func: str,
    value: Any = None,
    static_args: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        return call_with_warm_component(component, request(source, func, value, static_args))
    except WasmtimeError as exc:
        return {"ok": False, "error_type": type(exc).__name__, "error": str(exc)}


def run_no_host_wasi_probe(component: Component) -> dict[str, Any]:
    source = """
def transform(value):
    return {"doubled": value["n"] * 2}
"""
    result = call_with_bare_linker(component, request(source, "transform", {"n": 21}))
    assert result == {"ok": True, "value": {"doubled": 42}}, result
    return result


def run_probes(component: Component) -> dict[str, Any]:
    no_host_wasi = run_no_host_wasi_probe(component)

    namespace_source = """
counter = 0
def mutate(value):
    global counter
    counter += 1
    return counter
"""
    first = run_probe(component, namespace_source, "mutate")
    second = run_probe(component, namespace_source, "mutate")
    assert first == {"ok": True, "value": 1}, first
    assert second == {"ok": True, "value": 1}, second

    stdlib_source = """
def mutate(value):
    import json
    json._spike_counter = getattr(json, "_spike_counter", 0) + 1
    return json._spike_counter
"""
    first_stdlib = run_probe(component, stdlib_source, "mutate")
    second_stdlib = run_probe(component, stdlib_source, "mutate")
    assert first_stdlib == {"ok": True, "value": 1}, first_stdlib
    assert second_stdlib == {"ok": True, "value": 1}, second_stdlib

    clock_import_source = """
def probe(value):
    import time
    return sorted(name for name in ("time", "monotonic") if hasattr(time, name))
"""
    clock_time_source = """
def probe(value):
    import time
    return time.time()
"""
    clock_monotonic_source = """
def probe(value):
    import time
    return time.monotonic()
"""
    filesystem_read_source = """
def probe(value):
    return open("/etc/passwd").read(64)
"""
    filesystem_write_source = """
def probe(value):
    return open("x", "w").write("x")
"""
    socket_import_source = """
def probe(value):
    import socket
    return {"module": socket.__name__}
"""
    socket_connect_source = """
def probe(value):
    import socket
    sock = socket.create_connection(("example.com", 80), timeout=1)
    sock.close()
    return "connected"
"""
    urllib_import_source = """
def probe(value):
    import urllib.request
    return {"module": urllib.request.__name__}
"""
    urllib_open_source = """
def probe(value):
    import urllib.request
    return urllib.request.urlopen("http://example.com", timeout=1).read(1).decode()
"""
    clock = {
        "import_time": run_probe(component, clock_import_source, "probe"),
        "time_time": run_probe(component, clock_time_source, "probe"),
        "time_monotonic": run_probe(component, clock_monotonic_source, "probe"),
    }
    filesystem = {
        "read_etc_passwd": run_probe(component, filesystem_read_source, "probe"),
        "write_relative": run_probe(component, filesystem_write_source, "probe"),
    }
    network = {
        "import_socket": run_probe(component, socket_import_source, "probe"),
        "socket_connect": run_probe(component, socket_connect_source, "probe"),
        "import_urllib_request": run_probe(component, urllib_import_source, "probe"),
        "urllib_open": run_probe(component, urllib_open_source, "probe"),
    }
    assert not filesystem["read_etc_passwd"]["ok"], filesystem
    assert not filesystem["write_relative"]["ok"], filesystem
    assert not network["socket_connect"]["ok"], network
    assert not network["urllib_open"]["ok"], network

    return {
        "no_host_wasi": no_host_wasi,
        "state_exec_namespace": {"call_1": first, "call_2": second},
        "state_stdlib_module": {"call_1": first_stdlib, "call_2": second_stdlib},
        "clock": clock,
        "filesystem": filesystem,
        "network": network,
    }


def toolchain_info(component: Component) -> dict[str, Any]:
    version_source = """
def probe(value):
    import sys
    return {
        "version": sys.version,
        "platform": sys.platform,
        "executable": sys.executable,
    }
"""
    return {
        "componentize_py": metadata.version("componentize-py"),
        "wasmtime": metadata.version("wasmtime"),
        "host_python": sys.version,
        "component_python": run_probe(component, version_source, "probe"),
        "compiled_cache": "wasmtime.component.Component.serialize/deserialize_file",
    }


def mb(path: Path) -> float:
    return path.stat().st_size / 1_000_000


def print_table(results: dict[str, Any]) -> None:
    print("\nNumbers")
    print("| metric | value |")
    print("| --- | ---: |")
    print(f"| base component size MB | {results['sizes']['component_wasm_mb']:.3f} |")
    print(f"| compiled artifact size MB | {results['sizes']['compiled_cwasm_mb']:.3f} |")
    print(f"| componentize build s | {results['build']['componentize_build_s']:.3f} |")
    print(f"| compile+serialize s | {results['build']['compile_serialize_s']:.3f} |")
    for bench in results["benchmarks"]:
        print(f"| {bench['name']} median ms | {bench['median_ms']:.3f} |")
        print(f"| {bench['name']} p95 ms | {bench['p95_ms']:.3f} |")

    print("\nProbes")
    print(json.dumps(results["probes"], indent=2, sort_keys=True))


def main() -> None:
    build_timings = ensure_built()
    compiled_component = Component.deserialize_file(ENGINE, str(COMPILED))

    variant_a = benchmark(
        "variant_a_deserialize_file_plus_fresh_instance",
        call_with_deserialize,
    )
    variant_b = benchmark(
        "variant_b_warm_worker_fresh_instance",
        lambda payload: call_with_warm_component(compiled_component, payload),
    )
    probes = run_probes(compiled_component)
    results = {
        "calls_per_variant": CALLS,
        "budget_ms": 10.0,
        "host_path": "wasmtime-py in-process via wasmtime.component dynamic API",
        "toolchain": toolchain_info(compiled_component),
        "build": build_timings,
        "sizes": {
            "component_wasm_mb": mb(COMPONENT),
            "compiled_cwasm_mb": mb(COMPILED),
        },
        "benchmarks": [variant_a, variant_b],
        "breakdown": breakdown(compiled_component),
        "probes": probes,
        "go_no_go": {
            "fresh_per_call_with_deserialize_under_10ms": variant_a["p95_ms"] <= 10.0,
            "warm_worker_fresh_instance_under_10ms": variant_b["p95_ms"] <= 10.0,
        },
    }
    RESULTS.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
    print_table(results)


if __name__ == "__main__":
    main()
