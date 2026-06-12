from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

from wasmtime import Config, Engine
from wasmtime.component import Component

ROOT = Path(__file__).resolve().parent
WIT = ROOT / "wit" / "executor.wit"
SRC = ROOT / "src"
ARTIFACTS = ROOT / "artifacts"
COMPONENT = ARTIFACTS / "executor.wasm"
COMPILED = ARTIFACTS / "executor.cwasm"
METRICS = ARTIFACTS / "build_metrics.json"


def timed(command: list[str]) -> float:
    start = time.perf_counter()
    subprocess.run(command, cwd=ROOT, check=True)
    return time.perf_counter() - start


def build_component(force: bool = False) -> float:
    ARTIFACTS.mkdir(exist_ok=True)
    if COMPONENT.exists() and not force:
        return 0.0

    generated = SRC / "spike_executor.py"
    generated.unlink(missing_ok=True)
    command = [
        "componentize-py",
        "-d",
        str(WIT),
        "-w",
        "executor",
        "bindings",
        str(SRC),
    ]
    timed(command)

    return timed(
        [
            "componentize-py",
            "-d",
            str(WIT),
            "-w",
            "executor",
            "componentize",
            "--stub-wasi",
            "--python-path",
            str(SRC),
            "executor_component",
            "-o",
            str(COMPONENT),
        ]
    )


def engine() -> Engine:
    config = Config()
    config.wasm_component_model = True
    return Engine(config)


def compile_component(force: bool = False) -> float:
    if COMPILED.exists() and not force:
        return 0.0
    ARTIFACTS.mkdir(exist_ok=True)
    start = time.perf_counter()
    component = Component.from_file(engine(), str(COMPONENT))
    COMPILED.write_bytes(component.serialize())
    return time.perf_counter() - start


def ensure_built(force: bool = False) -> dict[str, float]:
    if COMPONENT.exists() and COMPILED.exists() and METRICS.exists() and not force:
        return json.loads(METRICS.read_text())

    build_time = build_component(force=force)
    compile_time = compile_component(force=force)
    timings = {
        "componentize_build_s": build_time,
        "compile_serialize_s": compile_time,
    }
    if build_time or compile_time or not METRICS.exists():
        METRICS.write_text(json.dumps(timings, indent=2, sort_keys=True) + "\n")
    return timings


if __name__ == "__main__":
    timings = ensure_built(force="--force" in sys.argv)
    for key, value in timings.items():
        print(f"{key}: {value:.3f}s")
