from __future__ import annotations

import pytest

pytest.importorskip("wasmtime")

from julep.errors import PureExecutionError
from julep.execution import wasm_executor
from julep.execution.wasm_executor import WasmExecutor, get_wasm_executor


def test_cache_file_uses_julep_prefix() -> None:
    executor = WasmExecutor()
    try:
        assert executor._cache_path().name.startswith("julep_executor_")
    finally:
        executor.close()


def test_trivial_pure_runs() -> None:
    source = """@pure("double")\ndef double(value, **kwargs):\n    return value * 2\n"""

    assert get_wasm_executor().run("double", source, 21, {}) == 42


def test_kwargs_passed() -> None:
    source = """@pure("scale")\ndef scale(value, *, factor=1):\n    return value * factor\n"""

    assert WasmExecutor().run("scale", source, 10, {"factor": 3}) == 30


def test_clock_fails_closed() -> None:
    source = """@pure("clock")\ndef clock(value, **kwargs):\n    import time\n    return time.time()\n"""

    with pytest.raises(PureExecutionError):
        WasmExecutor().run("clock", source, None, {})


def test_filesystem_fails_closed() -> None:
    source = """@pure("read")\ndef read(value, **kwargs):\n    return open("/etc/passwd").read(8)\n"""

    with pytest.raises(PureExecutionError):
        WasmExecutor().run("read", source, None, {})


def test_network_fails_closed() -> None:
    source = """@pure("network")\ndef network(value, **kwargs):\n    import socket\n    socket.create_connection(("example.com", 80), timeout=1)\n    return True\n"""

    with pytest.raises(PureExecutionError):
        WasmExecutor().run("network", source, None, {})


def test_no_cross_call_state_leak() -> None:
    source = """counter = 0\n@pure("bump")\ndef bump(value, **kwargs):\n    global counter\n    counter += 1\n    return counter\n"""
    executor = WasmExecutor()

    assert executor.run("bump", source, None, {}) == 1
    assert executor.run("bump", source, None, {}) == 1


def test_pure_exception_propagates_type() -> None:
    source = """@pure("explode")\ndef explode(value, **kwargs):\n    raise ValueError("boom")\n"""

    with pytest.raises(PureExecutionError) as exc:
        WasmExecutor().run("explode", source, None, {})

    assert exc.value.error_type == "ValueError"
    assert "boom" in exc.value.message


def test_oversized_request_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    source = """@pure("identity")\ndef identity(value, **kwargs):\n    return value\n"""
    monkeypatch.setattr(wasm_executor, "MAX_REQUEST_BYTES", 256)

    with pytest.raises(PureExecutionError) as excinfo:
        WasmExecutor().run("identity", source, "x" * 512, {})

    assert excinfo.value.error_type == "WasmInputTooLarge"


def test_oversized_request_is_rejected_before_json_materialization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = """@pure("identity")\ndef identity(value, **kwargs):\n    return value\n"""
    monkeypatch.setattr(wasm_executor, "MAX_REQUEST_BYTES", 256)
    original_dumps = wasm_executor.json.dumps
    materialized = False

    def tracking_dumps(*args, **kwargs):
        nonlocal materialized
        materialized = True
        return original_dumps(*args, **kwargs)

    monkeypatch.setattr(wasm_executor.json, "dumps", tracking_dumps)

    with pytest.raises(PureExecutionError) as excinfo:
        WasmExecutor().run("identity", source, "\x00" * 512, {})

    assert excinfo.value.error_type == "WasmInputTooLarge"
    assert not materialized


def test_oversized_response_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    source = """@pure("expand")\ndef expand(value, **kwargs):\n    return "x" * value\n"""
    monkeypatch.setattr(wasm_executor, "MAX_RESPONSE_BYTES", 256)

    with pytest.raises(PureExecutionError) as excinfo:
        WasmExecutor().run("expand", source, 512, {})

    assert excinfo.value.error_type == "WasmOutputTooLarge"


def test_guest_memory_is_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    source = """@pure("expand")\ndef expand(value, **kwargs):\n    return "x" * value\n"""
    monkeypatch.setattr(wasm_executor, "MAX_MEMORY_BYTES", 16 * 1024 * 1024)

    with pytest.raises(PureExecutionError) as excinfo:
        WasmExecutor().run("expand", source, 32 * 1024 * 1024, {})

    assert excinfo.value.error_type in {"MemoryError", "WasmSandboxTrap"}


def test_legacy_replay_bypasses_new_resource_limits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = """@pure("expand")\ndef expand(value, **kwargs):\n    return "x" * value\n"""
    monkeypatch.setattr(wasm_executor, "MAX_RESPONSE_BYTES", 256)
    monkeypatch.setattr(wasm_executor, "MAX_MEMORY_BYTES", 16 * 1024 * 1024)
    monkeypatch.setattr(wasm_executor, "_resource_limits_enabled", lambda: False)

    assert WasmExecutor().run("expand", source, 512, {}) == "x" * 512
