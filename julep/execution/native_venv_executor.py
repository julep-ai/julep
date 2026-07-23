"""Run granted dependency pures in uv-managed native virtualenvs."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
import threading
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .. import _env
from ..errors import PureExecutionError
from ..ir import canonical_json

_EXECUTOR: NativeVenvExecutor | None = None
_EXECUTOR_LOCK = threading.Lock()
_PYTHON_MAJOR_MINOR = re.compile(
    r"^\s*(?:~=|==|!=|<=|>=|<|>|===)?\s*(\d+)\.(\d+)(?:\.\d+)?"
)

_DRIVER = r"""
import json
import traceback

request = json.loads(input())
registry = {}

def pure(name):
    def deco(fn):
        registry[name] = fn
        return fn
    return deco

try:
    exec(request["source"], {"pure": pure})
    fn = registry[request["name"]]
    value = fn(request["value"], **(request.get("kwargs") or {}))
    print(json.dumps({"ok": True, "value": value}, sort_keys=True, separators=(",", ":")))
except BaseException as exc:
    print(json.dumps({
        "ok": False,
        "error_type": type(exc).__name__,
        "error": str(exc),
        "traceback_tail": traceback.format_exc().splitlines()[-8:],
    }, sort_keys=True, separators=(",", ":")))
"""


def get_native_venv_executor() -> NativeVenvExecutor:
    global _EXECUTOR
    if _EXECUTOR is None:
        with _EXECUTOR_LOCK:
            if _EXECUTOR is None:
                _EXECUTOR = NativeVenvExecutor()
    return _EXECUTOR


class NativeVenvExecutor:
    """Run source-only pures in cached uv virtualenv subprocesses."""

    def __init__(self, *, cache_dir: str | Path | None = None) -> None:
        root = cache_dir or _env.get(_env.JULEP_NATIVE_VENV_CACHE_DIR)
        self._cache_dir = Path(root) if root is not None else Path(tempfile.gettempdir())
        self._lock = threading.Lock()

    def run(
        self,
        name: str,
        source: str,
        value: Any,
        kwargs: dict[str, Any],
        *,
        deps: Sequence[str],
        requires_python: str | None = None,
    ) -> Any:
        dep_list = tuple(sorted(set(deps)))
        python = self._venv_python(name, dep_list, requires_python)
        request = {
            "kwargs": kwargs or {},
            "name": name,
            "source": source,
            "value": value,
        }
        try:
            proc = subprocess.run(
                [str(python), "-c", _DRIVER],
                input=json.dumps(request, sort_keys=True, separators=(",", ":")) + "\n",
                text=True,
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise self._subprocess_error(name, "native venv pure subprocess failed", e) from e
        except OSError as e:
            raise PureExecutionError(
                "NativeVenvError",
                f"native venv subprocess for pure {name!r} could not start: {e}",
                [f"NativeVenvError: {name}", str(e)],
            ) from e

        try:
            response = json.loads(proc.stdout)
        except json.JSONDecodeError as e:
            raise PureExecutionError(
                "NativeVenvError",
                f"native venv pure {name!r} returned non-JSON output",
                [f"NativeVenvError: {name}", proc.stdout[-500:], proc.stderr[-500:]],
            ) from e
        if not isinstance(response, dict):
            raise PureExecutionError(
                "NativeVenvError",
                f"native venv pure {name!r} returned a non-object response",
                [f"NativeVenvError: {name}"],
            )
        if response.get("ok"):
            return response.get("value")
        raise PureExecutionError(
            str(response.get("error_type", "NativeVenvPureError")),
            str(response.get("error", "")),
            self._traceback_tail(response.get("traceback_tail")),
        )

    def _venv_python(
        self,
        pure_name: str,
        deps: tuple[str, ...],
        requires_python: str | None,
    ) -> Path:
        venv = self._venv_path(deps, requires_python)
        python = venv / "bin" / "python"
        if python.exists():
            return python

        with self._lock:
            if python.exists():
                return python
            venv.parent.mkdir(parents=True, exist_ok=True)
            command = ["uv", "venv", str(venv)]
            python_request = self._python_request(requires_python)
            if python_request is not None:
                command.extend(["--python", python_request])
            self._run_uv(command, pure_name, "create native dependency venv")
            if deps:
                self._run_uv(
                    ["uv", "pip", "install", "--python", str(python), *deps],
                    pure_name,
                    "install native dependency deps",
                )
        return python

    def _venv_path(self, deps: tuple[str, ...], requires_python: str | None) -> Path:
        payload = {
            "deps": list(deps),
            "requiresPython": requires_python,
        }
        digest = hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()[:24]
        return self._cache_dir / f"julep_native_venv_{digest}"

    def _run_uv(self, command: list[str], pure_name: str, action: str) -> None:
        try:
            subprocess.run(command, text=True, capture_output=True, check=True)
        except FileNotFoundError as e:
            raise PureExecutionError(
                "NativeVenvUnavailable",
                f"uv is not available; pure {pure_name!r} requires the native dependency "
                "tier. Install uv on the worker image or remove the native grant.",
                [f"NativeVenvUnavailable: {pure_name}", "uv"],
            ) from e
        except subprocess.CalledProcessError as e:
            raise self._subprocess_error(pure_name, f"uv failed to {action}", e) from e

    @staticmethod
    def _python_request(requires_python: str | None) -> str | None:
        if requires_python is None:
            return None
        match = _PYTHON_MAJOR_MINOR.match(requires_python)
        if match is None:
            return requires_python
        return f"{match.group(1)}.{match.group(2)}"

    def _subprocess_error(
        self,
        pure_name: str,
        prefix: str,
        error: subprocess.CalledProcessError[str],
    ) -> PureExecutionError:
        tail = self._process_tail(error.stdout, error.stderr)
        return PureExecutionError(
            "NativeVenvError",
            f"{prefix} for pure {pure_name!r}: {'; '.join(tail) or error}",
            [f"NativeVenvError: {pure_name}", *tail],
        )

    @staticmethod
    def _process_tail(stdout: str | None, stderr: str | None) -> list[str]:
        lines: list[str] = []
        for stream in (stdout, stderr):
            if stream:
                lines.extend(line.strip() for line in stream.splitlines() if line.strip())
        return lines[-6:]

    @staticmethod
    def _traceback_tail(value: object) -> list[str]:
        if isinstance(value, list) and all(isinstance(item, str) for item in value):
            return value[-8:]
        return []
