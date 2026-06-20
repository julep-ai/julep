from __future__ import annotations

import pytest

from composable_agents.errors import PureExecutionError
from composable_agents.execution.wasm_executor import WasmExecutor, get_wasm_executor


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
