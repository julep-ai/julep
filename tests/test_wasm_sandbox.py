"""Adversarial sandbox probes: a bundle-sourced pure that reaches for the clock,
the filesystem, the network, or any host capability FAILS CLOSED, and the failure
is surfaced as a structured, operator-actionable diagnostic — not a bare,
backtrace-dumping ``WasmtimeError``.

The wasm tier builds the CPython component with ``--stub-wasi`` (no WASI imports),
so any host-capability syscall executes a wasm ``unreachable`` and traps at the
host boundary. The host (``WasmExecutor.run``) classifies that trap into a
:class:`~julep.errors.PureExecutionError` whose ``error_type`` is a
stable, greppable tag (``WasmSandboxTrap`` / ``WasmFuelExhausted`` /
``WasmDeadlineExceeded``) and whose message names the offending pure and points
the operator at the runbook — matching the house convention that a failure carries
a structured, actionable diagnostic rather than an opaque engine error.

This module also pins the determinism guarantee: module-level state a pure mutates
in one call has NO observable effect on the next call (fresh instance per call).
"""

from __future__ import annotations

import json

import pytest

pytest.importorskip("wasmtime")

from julep.errors import JulepError, PureExecutionError
from julep.execution.wasm_executor import WasmExecutor

# Each probe is a bundle-shippable pure (the @pure(name) shim is replicated in the
# wasm component) that attempts a forbidden host capability and must trap.
CLOCK_PROBE = (
    '@pure("probe.clock")\n'
    "def probe(value, **kwargs):\n"
    "    import time\n"
    "    return time.time()\n"
)
MONOTONIC_PROBE = (
    '@pure("probe.monotonic")\n'
    "def probe(value, **kwargs):\n"
    "    import time\n"
    "    return time.monotonic()\n"
)
FILESYSTEM_READ_PROBE = (
    '@pure("probe.fs_read")\n'
    "def probe(value, **kwargs):\n"
    '    return open("/etc/passwd").read(16)\n'
)
FILESYSTEM_WRITE_PROBE = (
    '@pure("probe.fs_write")\n'
    "def probe(value, **kwargs):\n"
    '    with open("/tmp/cad-wasm-escape", "w") as fh:\n'
    '        fh.write("escaped")\n'
    "    return True\n"
)
FILESYSTEM_LIST_PROBE = (
    '@pure("probe.fs_list")\n'
    "def probe(value, **kwargs):\n"
    "    import os\n"
    '    return os.listdir("/")\n'
)
NETWORK_PROBE = (
    '@pure("probe.network")\n'
    "def probe(value, **kwargs):\n"
    "    import socket\n"
    '    socket.create_connection(("example.com", 80), timeout=1)\n'
    "    return True\n"
)
RANDOM_ENTROPY_PROBE = (
    '@pure("probe.entropy")\n'
    "def probe(value, **kwargs):\n"
    "    import os\n"
    "    return os.urandom(8).hex()\n"
)
ENV_PROBE = (
    '@pure("probe.env")\n'
    "def probe(value, **kwargs):\n"
    "    import os\n"
    '    return os.environ.get("PATH")\n'
)

# (probe-name, source) — each must fail closed as a wasm sandbox trap.
CAPABILITY_PROBES = [
    ("probe.clock", CLOCK_PROBE),
    ("probe.monotonic", MONOTONIC_PROBE),
    ("probe.fs_read", FILESYSTEM_READ_PROBE),
    ("probe.fs_write", FILESYSTEM_WRITE_PROBE),
    ("probe.fs_list", FILESYSTEM_LIST_PROBE),
    ("probe.network", NETWORK_PROBE),
    ("probe.entropy", RANDOM_ENTROPY_PROBE),
]


@pytest.fixture(scope="module")
def executor() -> WasmExecutor:
    return WasmExecutor()


@pytest.mark.parametrize("name,source", CAPABILITY_PROBES, ids=[p[0] for p in CAPABILITY_PROBES])
def test_capability_probe_fails_closed_with_structured_diagnostic(
    executor: WasmExecutor, name: str, source: str
) -> None:
    """Clock / filesystem / network / entropy probes trap, surfaced as a
    PureExecutionError with an operator-actionable, span-bearing diagnostic."""
    with pytest.raises(PureExecutionError) as excinfo:
        executor.run(name, source, None, {})

    err = excinfo.value

    # House style: it is a JulepError (the framework's own hierarchy),
    # NOT a leaked wasmtime engine error.
    assert isinstance(err, JulepError)
    assert type(err).__module__.startswith("julep")

    # Structured, greppable classification — NOT a bare WasmtimeError tag.
    assert err.error_type == "WasmSandboxTrap", err.error_type
    assert err.error_type != "WasmtimeError"

    # Operator-actionable message: names the offending pure, explains the policy,
    # and points at the runbook.
    assert name in err.message
    assert "wasm sandbox" in err.message
    assert "clock, filesystem, network" in err.message
    assert "docs/ops/wasm-tier-runbook.md" in err.message

    # Carries a short structured tail for diagnosis (the classification + the raw
    # trap line) rather than dumping the full multi-line wasm backtrace.
    assert err.traceback_tail
    assert len(err.traceback_tail) <= 3
    assert err.traceback_tail[0] == f"WasmSandboxTrap: {name}"
    assert any("wasm trap" in line.lower() for line in err.traceback_tail)


def test_env_access_is_not_an_observable_escape(executor: WasmExecutor) -> None:
    """A pure reading ``os.environ`` may not observe the host environment: it
    either traps or returns a non-host value. Either way no host secret leaks."""
    try:
        result = executor.run("probe.env", ENV_PROBE, None, {})
    except PureExecutionError as err:
        # Trapping is the strong outcome (no host env at all).
        assert err.error_type in {"WasmSandboxTrap", "WasmHostError"}
        return
    # If it returns at all, it must NOT be the host PATH.
    import os

    assert result != os.environ.get("PATH")


def test_traceback_tail_does_not_leak_full_backtrace(executor: WasmExecutor) -> None:
    """The structured diagnostic must NOT smuggle the noisy multi-line wasm
    backtrace into the message — operators get a clean, actionable line."""
    with pytest.raises(PureExecutionError) as excinfo:
        executor.run("probe.clock", CLOCK_PROBE, None, {})

    err = excinfo.value
    # The raw engine backtrace is a multi-line "wasm backtrace:\n    0: ..." dump;
    # the surfaced message must be a single actionable sentence, not that dump.
    assert "wasm backtrace" not in err.message
    assert err.message.count("\n") == 0


def test_fuel_exhaustion_is_a_structured_resource_diagnostic() -> None:
    """A runaway (infinite-loop) pure exhausts fuel and surfaces a distinct,
    actionable resource diagnostic — not a generic sandbox trap."""
    import os

    prev = os.environ.get("JULEP_WASM_FUEL")
    os.environ["JULEP_WASM_FUEL"] = "200000"
    try:
        executor = WasmExecutor()
    finally:
        if prev is None:
            os.environ.pop("JULEP_WASM_FUEL", None)
        else:
            os.environ["JULEP_WASM_FUEL"] = prev

    spin = (
        '@pure("probe.spin")\n'
        "def probe(value, **kwargs):\n"
        "    n = 0\n"
        "    while True:\n"
        "        n += 1\n"
        "    return n\n"
    )
    with pytest.raises(PureExecutionError) as excinfo:
        executor.run("probe.spin", spin, None, {})

    err = excinfo.value
    assert err.error_type == "WasmFuelExhausted", err.error_type
    assert "probe.spin" in err.message
    assert "fuel" in err.message.lower()


# Run the epoch probe in a FRESH subprocess. The epoch backstop spawns a
# wall-clock ticker thread that calls into wasmtime's native layer; letting that
# thread coexist with other tests' wasmtime object teardown in the same process
# races the native allocator and can crash the interpreter. Isolating the whole
# engine + ticker lifecycle in a subprocess makes the test deterministic and
# leak-free, and also mirrors how a real worker runs one process-global executor.
_EPOCH_SUBPROCESS = '''
import json
import os

os.environ["JULEP_WASM_EPOCH_MS"] = "10"
os.environ["JULEP_WASM_FUEL"] = str(20_000_000_000)  # huge: epoch trips, not fuel

from julep.errors import PureExecutionError
from julep.execution.wasm_executor import WasmExecutor

spin = (
    \'@pure("probe.spin.epoch")\\n\'
    "def probe(value, **kwargs):\\n"
    "    n = 0\\n"
    "    while True:\\n"
    "        n += 1\\n"
    "    return n\\n"
)

executor = WasmExecutor()
try:
    executor.run("probe.spin.epoch", spin, None, {})
    print(json.dumps({"raised": False}))
except PureExecutionError as err:
    print(json.dumps({"raised": True, "error_type": err.error_type, "message": err.message}))
finally:
    executor.close()
'''


def test_epoch_deadline_is_a_structured_resource_diagnostic() -> None:
    """When the OPT-IN epoch backstop is enabled (JULEP_WASM_EPOCH_MS), a
    long-running pure that outlives the deadline traps and surfaces a distinct,
    actionable WasmDeadlineExceeded diagnostic.

    NOTE: epoch is a coarse, NON-deterministic, wall-clock backstop — fuel is the
    deterministic, always-on primary bound (see the runbook). This test merely
    pins that the epoch path classifies correctly when explicitly enabled; epoch
    is off by default and must never be the determinism mechanism.
    """
    import subprocess
    import sys

    proc = subprocess.run(
        [sys.executable, "-c", _EPOCH_SUBPROCESS],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, f"subprocess failed: {proc.stderr}"
    result = json.loads(proc.stdout.strip().splitlines()[-1])
    assert result["raised"] is True, "epoch-bounded spin pure must trap"
    assert result["error_type"] == "WasmDeadlineExceeded", result["error_type"]
    assert "probe.spin.epoch" in result["message"]
    assert "epoch" in result["message"].lower()


def test_cross_call_module_state_has_no_observable_effect(executor: WasmExecutor) -> None:
    """Determinism: a module-level counter a pure mutates in call N is reset for
    call N+1 (fresh wasm instance per call) — no cross-call state leak."""
    source = (
        "counter = 0\n"
        '@pure("probe.bump")\n'
        "def probe(value, **kwargs):\n"
        "    global counter\n"
        "    counter += 1\n"
        "    return counter\n"
    )
    first = executor.run("probe.bump", source, None, {})
    second = executor.run("probe.bump", source, None, {})
    third = executor.run("probe.bump", source, None, {})

    # Every call starts from a pristine module state: always 1, never 1/2/3.
    assert first == second == third == 1


def test_sandbox_trap_diagnostic_reaches_the_projection_failed_event() -> None:
    """A wasm sandbox trap must surface its STRUCTURED diagnostic on the
    projection/emitter FAILED event (and thus the span), not the bare literal
    'framework-error'. PureExecutionError is a JulepError, so without
    special-casing it the interpreter would record 'framework-error' and drop the
    actionable error_type/message the host so carefully built.
    """
    import asyncio

    from julep import arr
    from julep.execution.interpreter import InMemoryEnv, interpret
    from julep.projection import InMemoryProjection, ProjectionEmitter
    from julep.registry import Registry

    # A bundle-sourced (wasm-tier) pure that reaches for the clock and traps.
    reg = Registry()
    reg.register_pure_from_source("probe.clock", CLOCK_PROBE)

    projection = InMemoryProjection()
    env = InMemoryEnv({}, ProjectionEmitter(projection), registry=reg)
    flow = arr("probe.clock")

    with pytest.raises(PureExecutionError) as excinfo:
        asyncio.run(interpret(flow, None, env))

    err = excinfo.value
    assert err.error_type == "WasmSandboxTrap"

    failures = projection.failures()
    assert len(failures) == 1
    failed = failures[0]
    # The reason carries the structured error_type + message, NOT 'framework-error'.
    assert failed.error != "framework-error"
    assert failed.error == f"{err.error_type}: {err.message}"
    assert "WasmSandboxTrap" in failed.error
    assert "probe.clock" in failed.error


def test_mutated_default_arg_does_not_persist_across_calls(executor: WasmExecutor) -> None:
    """The classic mutable-default-argument leak cannot cross calls either: the
    function object is rebuilt from source in a fresh instance every call."""
    source = (
        '@pure("probe.acc")\n'
        "def probe(value, acc=[]):\n"
        "    acc.append(value)\n"
        "    return list(acc)\n"
    )
    assert executor.run("probe.acc", source, "a", {}) == ["a"]
    assert executor.run("probe.acc", source, "b", {}) == ["b"]
