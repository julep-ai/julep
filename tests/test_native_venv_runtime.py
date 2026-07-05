from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

from julep.errors import PureExecutionError
from julep.execution import native_venv_executor
from julep.execution.native_venv_executor import NativeVenvExecutor
from julep.registry import Registry

pytestmark = pytest.mark.skipif(
    shutil.which("uv") is None,
    reason="uv is not installed; native venv tier cannot run",
)


def _source(name: str, body: str) -> str:
    return f'@pure("{name}")\n{body}'


def _stdlib_source(name: str) -> str:
    return _source(
        name,
        "def transform(value, **kwargs):\n"
        "    import math\n"
        "    n = int(value['n'])\n"
        "    return {'n': n, 'sqrt': math.isqrt(n), 'digits': list(str(n))}\n",
    )


def test_native_venv_runs_stdlib_pure_end_to_end(tmp_path: Path) -> None:
    name = "native.runtime.stdlib.v1"
    executor = NativeVenvExecutor(cache_dir=tmp_path)

    result = executor.run(
        name,
        _stdlib_source(name),
        {"n": 144},
        {},
        deps=(),
        requires_python=">=3.11",
    )

    assert result == {"digits": ["1", "4", "4"], "n": 144, "sqrt": 12}


def test_native_venv_round_trips_deterministically(tmp_path: Path) -> None:
    name = "native.runtime.deterministic.v1"
    source = _stdlib_source(name)
    executor = NativeVenvExecutor(cache_dir=tmp_path)

    first = executor.run(name, source, {"n": 225}, {}, deps=(), requires_python=">=3.11")
    venvs = list(tmp_path.glob("composable_native_venv_*"))
    assert len(venvs) == 1
    assert (venvs[0] / "bin" / "python").exists()

    second = executor.run(name, source, {"n": 225}, {}, deps=(), requires_python=">=3.11")
    changed = executor.run(name, source, {"n": 196}, {}, deps=(), requires_python=">=3.11")

    assert second == first
    assert changed == {"digits": ["1", "9", "6"], "n": 196, "sqrt": 14}
    assert changed != first
    assert list(tmp_path.glob("composable_native_venv_*")) == venvs


def test_native_venv_kwargs_round_trip(tmp_path: Path) -> None:
    name = "native.runtime.kwargs.v1"
    source = _source(
        name,
        "def scale(value, **kwargs):\n"
        "    return {'v': value, 'scale': value * kwargs['factor']}\n",
    )
    executor = NativeVenvExecutor(cache_dir=tmp_path)

    result = executor.run(
        name,
        source,
        7,
        {"factor": 3},
        deps=(),
        requires_python=">=3.11",
    )

    assert result == {"scale": 21, "v": 7}


def test_native_venv_subprocess_error_is_structured(tmp_path: Path) -> None:
    name = "native.runtime.error.v1"
    source = _source(
        name,
        "def explode(value, **kwargs):\n"
        "    raise ValueError('boom')\n",
    )
    executor = NativeVenvExecutor(cache_dir=tmp_path)

    with pytest.raises(PureExecutionError) as excinfo:
        executor.run(name, source, None, {}, deps=(), requires_python=">=3.11")

    assert excinfo.value.error_type == "ValueError"
    assert "boom" in excinfo.value.message
    assert any("ValueError" in line for line in excinfo.value.traceback_tail)


def test_native_venv_missing_uv_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    name = "native.runtime.missing_uv.v1"
    executor = NativeVenvExecutor(cache_dir=tmp_path)

    def fake_run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if command and command[0] == "uv":
            raise FileNotFoundError("uv")
        raise AssertionError(f"unexpected command: {command!r}")

    monkeypatch.setattr(native_venv_executor.subprocess, "run", fake_run)

    with pytest.raises(PureExecutionError) as excinfo:
        executor.run(name, _stdlib_source(name), {"n": 9}, {}, deps=(), requires_python=">=3.11")

    assert excinfo.value.error_type == "NativeVenvUnavailable"
    assert name in excinfo.value.message
    assert "uv" in excinfo.value.message
    assert "uv" in excinfo.value.traceback_tail


def test_native_venv_third_party_install_leg(tmp_path: Path) -> None:
    name = "native.runtime.third_party.v1"
    source = _source(
        name,
        "def import_dep(value, **kwargs):\n"
        "    import six\n"
        "    return {'text': six.ensure_text(value['text']), 'six': six.PY3}\n",
    )
    executor = NativeVenvExecutor(cache_dir=tmp_path)

    try:
        result = executor.run(
            name,
            source,
            {"text": "ok"},
            {},
            deps=("six==1.17.0",),
            requires_python=">=3.11",
        )
    except PureExecutionError as exc:
        if exc.error_type == "NativeVenvError":
            pytest.skip(f"native dep install needs network: {exc}")
        raise

    assert result == {"six": True, "text": "ok"}


def test_native_venv_routes_through_registry_get_pure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    name = "native.runtime.registry.v1"
    source = _source(
        name,
        "def double(value, **kwargs):\n"
        "    return {'value': value, 'doubled': value * 2}\n",
    )
    registry = Registry()
    registry.register_pure_from_source(name, source, tier="native_venv")
    monkeypatch.setenv("COMPOSABLE_NATIVE_VENV_CACHE_DIR", str(tmp_path))
    monkeypatch.setattr(native_venv_executor, "_EXECUTOR", None)

    result = registry.get_pure(name)(11)

    assert result == {"doubled": 22, "value": 11}
    assert list(tmp_path.glob("composable_native_venv_*"))
