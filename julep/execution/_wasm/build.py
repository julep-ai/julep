"""Build the vendored wasm executor component.

Run with:
    uv run --with componentize-py python julep/execution/_wasm/build.py

``executor.wasm`` is the committed vendored base component. The ``.cwasm`` cache
is not committed because it is wasmtime-version and platform specific.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WIT = ROOT / "wit" / "executor.wit"
COMPONENT = ROOT / "executor.wasm"


def build_component(force: bool = False) -> None:
    if COMPONENT.exists() and not force:
        return

    subprocess.run(
        [
            "componentize-py",
            "-d",
            str(WIT),
            "-w",
            "executor",
            "bindings",
            str(ROOT),
        ],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [
            "componentize-py",
            "-d",
            str(WIT),
            "-w",
            "executor",
            "componentize",
            "--stub-wasi",
            "--python-path",
            str(ROOT),
            "executor_component",
            "-o",
            str(COMPONENT),
        ],
        cwd=ROOT,
        check=True,
    )


if __name__ == "__main__":
    build_component(force="--force" in sys.argv)
    print(f"{COMPONENT} ({COMPONENT.stat().st_size} bytes)")
