# DBOS Backend + Flow-Runtime Extensions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a DBOS execution backend to composable_agents plus the four flow-runtime features mem-mcp needs to author all of its pipelines as frozen flows: a durable timer leaf, flow continuation (chaining), bounded fan-out, and a pluggable projection sink — with the dispatch boundary documented as a first-class spec concept.

**Architecture:** The interpreter (`composable_agents/execution/interpreter.py`) is already engine-agnostic: every effect goes through the injected `Env` protocol, and Temporal coupling lives only in `harness.py`/`activities.py`/`worker.py`. We (1) extract the backend-neutral effect implementations out of `activities.py` into a new `effects.py` so a non-Temporal backend can reuse them, (2) add the four runtime features to the pure core + both existing envs, then (3) build `dbos_backend.py`: DBOS `@step`s wrapping the effects, a `DbosEnv`, a `flow_workflow` DBOS workflow that runs `interpret`, and a chaining runner. Race/hedge/quorum and `app` (agent-loop) nodes are explicitly rejected at dispatch time on DBOS in v1 (DBOS cannot cancel in-flight steps; the agent loop port is a follow-up).

**Tech Stack:** Python ≥3.10 core (DBOS module requires the consumer's Python; mem-mcp is 3.13), `dbos>=2.18` (new optional extra), existing `temporalio>=1.7` extra untouched. Tests: pytest; DBOS integration tests need a Postgres URL via `DBOS_TEST_DATABASE_URL` (skip otherwise), mirroring how Temporal tests skip without `temporalio`.

**Verification gates (run after every task):**
- `python -m pytest` (not bare `pytest`)
- `uv run mypy --strict composable_agents` (package only; `composable_agents/execution/*` is exempted via the pyproject override — keep new execution modules under that override, but new *pure-core* files must pass strict)
- `ruff check composable_agents tests`

**Out of scope (follow-up plans, do not build here):**
- The mem-mcp adoption plan (capability manifests in CI, Logfire/Langfuse sink adapters, pipeline conversions) — separate plan in the mem-mcp repo.
- `AgentWorkflow` (the App loop) on DBOS — v1 rejects `Op.APP` on the DBOS backend.
- race/hedge/quorum on DBOS — requires cancellation semantics DBOS doesn't have.

---

## File Structure

| File | Status | Responsibility |
|---|---|---|
| `composable_agents/execution/effects.py` | create | Backend-neutral effect implementations + `WorkerContext`/`configure` (moved from activities.py), no temporalio import |
| `composable_agents/execution/activities.py` | rewrite | Thin `@activity.defn` wrappers delegating to effects.py; re-exports for backward compat |
| `composable_agents/execution/policy.py` | create | `ExecutionPolicy` (moved from harness.py so DBOS can import it without temporalio) |
| `composable_agents/ir.py` | modify | `SLEEP_TOOL` reserved native constant |
| `composable_agents/freeze.py` | modify | Synthetic resolution for `SLEEP_TOOL` (mirrors human gate) |
| `composable_agents/derived.py` | modify | `delay(*, seconds)` combinator |
| `composable_agents/execution/interpreter.py` | modify | `Env.sleep`, sleep special-case in `_eval_prim`, `InMemoryEnv.sleep`, `gather_bounded` |
| `composable_agents/continuation.py` | create | Continuation sentinel helpers + `run_chained` (pure core, strict mypy) |
| `composable_agents/execution/harness.py` | modify | `_TemporalEnv.sleep`, bounded gather, continue-as-new on continuation; import `ExecutionPolicy` from policy.py |
| `composable_agents/projection.py` | modify | `ProjectionSink` protocol + `TeeStore` |
| `composable_agents/errors.py` | modify | `UnsupportedShapeError` |
| `composable_agents/execution/dbos_backend.py` | create | DBOS steps, `DbosEnv`, `flow_workflow`, `run_flow_dbos`, `submit_human_dbos`, shape scan, sink config |
| `composable_agents/execution/__init__.py` | modify | `HAVE_DBOS` + lazy DBOS exports |
| `composable_agents/__init__.py` | modify | Export `delay`, continuation helpers, `HAVE_DBOS` |
| `pyproject.toml` | modify | `dbos` extra; `dbos>=2.18` in dev |
| `docs/dispatch-boundary.md` | create | The dispatch/processing split as a spec concept |
| `docs/deploy-dbos.md` | create | Running flows on DBOS |
| `docs/SPEC.md` | modify | Reserved `__sleep__` tool, continuation convention, dispatch boundary pointer |
| `tests/test_effects_extraction.py` | create | effects.py importable without temporalio; behavior parity |
| `tests/test_delay.py` | create | delay leaf: in-memory, freeze, value pass-through |
| `tests/test_continuation.py` | create | sentinel helpers + `run_chained` |
| `tests/test_bounded_gather.py` | create | `gather_bounded` concurrency ceiling |
| `tests/test_projection_tee.py` | create | TeeStore fan-out + emitter compatibility |
| `tests/test_dbos_api_spike.py` | create | Raw dbos-2.18 API conformance (gated) |
| `tests/test_dbos_pure.py` | create | shape scan, policy-error envelope, retry-variant choice (no DB) |
| `tests/test_e2e_dbos.py` | create | Full flows on DBOS: seq, delay, gate, continuation, bounded par (gated) |
| `tests/test_e2e_temporal_continuation.py` | create | continue-as-new chaining + durable delay on Temporal (gated) |

---

### Task 1: Extract the backend-neutral effects layer

The DBOS backend must reuse the effect implementations (`callTool`, `invokeReasoner`, `compilePlan`, `verifyPures`, `resolveSubflow`, `resolveRuntimeCapabilities`, `resolveAgentSpec`, `loadState`, `commitState`, `putBlob`) and `WorkerContext`/`configure` without importing `temporalio`. Also move `ExecutionPolicy` (pure dataclass) out of harness.py, and move `_toolref_json_from_key` to effects.py as `toolref_json_from_key`.

**Files:**
- Create: `composable_agents/execution/effects.py`
- Create: `composable_agents/execution/policy.py`
- Rewrite: `composable_agents/execution/activities.py`
- Modify: `composable_agents/execution/harness.py` (imports only)
- Test: `tests/test_effects_extraction.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_effects_extraction.py
"""The effects layer must be importable and usable without temporalio."""
from __future__ import annotations

import asyncio
import subprocess
import sys


def test_effects_importable_without_temporalio():
    code = (
        "import builtins\n"
        "real_import = builtins.__import__\n"
        "def block(name, *a, **k):\n"
        "    if name.split('.')[0] == 'temporalio':\n"
        "        raise ImportError('temporalio blocked by test')\n"
        "    return real_import(name, *a, **k)\n"
        "builtins.__import__ = block\n"
        "import composable_agents.execution.effects\n"
        "import composable_agents.execution.policy\n"
        "print('ok')\n"
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    assert "ok" in out.stdout


def test_run_call_effect_routes_mcp():
    from composable_agents.execution.effects import (
        CallToolInput, WorkerContext, callTool, configure,
    )

    seen = {}

    async def fake_mcp(server, tool, value, key):
        seen.update(server=server, tool=tool, value=value, key=key)
        return {"hits": 3}

    configure(WorkerContext(mcp_call=fake_mcp))
    inp = CallToolInput(
        tool_ref={"kind": "mcp", "server": "kb", "tool": "search"},
        value={"q": "x"}, cid="cid-1",
    )
    result = asyncio.run(callTool(inp))
    assert result == {"hits": 3}
    assert seen == {"server": "kb", "tool": "search", "value": {"q": "x"}, "key": "cid-1"}


def test_toolref_json_roundtrip():
    from composable_agents.execution.effects import toolref_json_from_key

    assert toolref_json_from_key("kb/search") == {"kind": "mcp", "server": "kb", "tool": "search"}
    assert toolref_json_from_key("fetch") == {"kind": "native", "name": "fetch"}


def test_activities_reexport_worker_context():
    # Backward compat: existing imports from .activities keep working.
    from composable_agents.execution.activities import WorkerContext as A
    from composable_agents.execution.effects import WorkerContext as E

    assert A is E
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_effects_extraction.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'composable_agents.execution.effects'`

- [ ] **Step 3: Create `composable_agents/execution/policy.py`**

Move the `ExecutionPolicy` dataclass verbatim from `composable_agents/execution/harness.py:91-137` into the new module:

```python
# composable_agents/execution/policy.py
"""Tunable execution policy shared by all execution backends (a §6 open seam).

Pure dataclass + JSON codec; no engine imports, so the Temporal harness and the
DBOS backend both consume it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class ExecutionPolicy:
    # ... body moved VERBATIM from harness.py lines 92-137 (fields, to_json,
    # from_json) — do not retype it, cut and paste, no edits ...
```

- [ ] **Step 4: Create `composable_agents/execution/effects.py`**

Move from `composable_agents/execution/activities.py` into `effects.py`, **verbatim except the listed edits**: the module docstring's first paragraph (reword as below), `McpCaller`/`LlmCaller` aliases (lines 46-47), `WorkerContext` (50-75), `_CTX`/`configure`/`_registry`/`_domain_of` (78-94), all six input dataclasses (100-142), all ten effect functions (148-408) **with their `@activity.defn(...)` decorator lines deleted**, and the private helpers `_approval_value`/`_contract_payload`/`_grant_contract_payload`/`_normalize_contract_payload` (291-330). Edits:

1. New header + imports — drop `from temporalio import activity`, add a logger:

```python
# composable_agents/execution/effects.py
"""Backend-neutral effect implementations (the Tools + Reasoners boundary).

These are the bodies of the Temporal activities, factored out so any durable
backend (Temporal, DBOS) can wrap them in its own retry/checkpoint unit.
This module must never import an engine: no temporalio, no dbos.
Configuration is process-global via :func:`configure` (one WorkerContext per
worker process), exactly as before.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Optional

from .. import agent_loop as al
from ..capabilities import CapabilityManifest, ToolGrant
from ..contracts import CONSERVATIVE_DEFAULT, ToolContract
from ..dotctx import Reasoner
from ..errors import CapabilityDenied, PureDriftError
from ..ir import Node, toolref_from_json, toolref_key
from ..kinds import Effect, Idempotency
from ..registry import DEFAULT_REGISTRY, Registry
from ..prompt import rendered_reasoner_for
from ..staged import admit_plan
from .blobstore import BlobStore
from .session_store import SessionStore

logger = logging.getLogger("composable_agents.execution.effects")
```

2. In `callTool`, replace `activity.logger.debug("callTool %s -> %s", key, url)` with `logger.debug("callTool %s -> %s", key, url)`.

3. Append the relocated key-to-ref helper (moved from `harness.py:175-186`, made public):

```python
def toolref_json_from_key(key: str) -> dict[str, Any]:
    """Reverse of :func:`~composable_agents.ir.toolref_key`.

    ``"server/tool"`` is an MCP tool; a bare name is a native tool.
    """
    if "/" in key:
        server, tool = key.split("/", 1)
        return {"kind": "mcp", "server": server, "tool": tool}
    return {"kind": "native", "name": key}
```

- [ ] **Step 5: Rewrite `composable_agents/execution/activities.py` as thin wrappers**

Replace the whole file with:

```python
# composable_agents/execution/activities.py
"""Temporal activity wrappers over the backend-neutral effects layer.

Each activity delegates to :mod:`composable_agents.execution.effects`; the
effect bodies hold all IO and configuration. This module is the only one of
the pair that imports temporalio, so it stays behind the HAVE_TEMPORAL guard.
"""

from __future__ import annotations

from typing import Any

from temporalio import activity

# Re-exports: every public name that previously lived here.
from .effects import (
    CallToolInput as CallToolInput,
    CommitStateInput as CommitStateInput,
    CompilePlanInput as CompilePlanInput,
    InvokeReasonerInput as InvokeReasonerInput,
    LlmCaller as LlmCaller,
    LoadStateInput as LoadStateInput,
    McpCaller as McpCaller,
    PutBlobInput as PutBlobInput,
    WorkerContext as WorkerContext,
    configure as configure,
)
from . import effects


@activity.defn(name="loadState")
async def loadState(inp: LoadStateInput) -> dict[str, Any]:
    return await effects.loadState(inp)


@activity.defn(name="commitState")
async def commitState(inp: CommitStateInput) -> int:
    return await effects.commitState(inp)


@activity.defn(name="putBlob")
async def putBlob(inp: PutBlobInput) -> str:
    return await effects.putBlob(inp)


@activity.defn(name="callTool")
async def callTool(inp: CallToolInput) -> Any:
    return await effects.callTool(inp)


@activity.defn(name="invokeReasoner")
async def invokeReasoner(inp: InvokeReasonerInput) -> Any:
    return await effects.invokeReasoner(inp)


@activity.defn(name="compilePlan")
async def compilePlan(inp: CompilePlanInput) -> dict[str, Any]:
    return await effects.compilePlan(inp)


@activity.defn(name="verifyPures")
async def verifyPures(pinned: dict[str, str]) -> None:
    return await effects.verifyPures(pinned)


@activity.defn(name="resolveSubflow")
async def resolveSubflow(ref: str) -> dict[str, Any]:
    return await effects.resolveSubflow(ref)


@activity.defn(name="resolveRuntimeCapabilities")
async def resolveRuntimeCapabilities() -> dict[str, Any]:
    return await effects.resolveRuntimeCapabilities()


@activity.defn(name="resolveAgentSpec")
async def resolveAgentSpec(controller: str) -> dict[str, Any]:
    return await effects.resolveAgentSpec(controller)
```

- [ ] **Step 6: Update `harness.py` imports**

In `composable_agents/execution/harness.py`:
1. Delete the `ExecutionPolicy` class body (lines 91-137) and `_toolref_json_from_key` (lines 175-186).
2. Inside the `with workflow.unsafe.imports_passed_through():` block, add:

```python
    from .policy import ExecutionPolicy
    from .effects import toolref_json_from_key as _toolref_json_from_key
```

(Keeping the `_toolref_json_from_key` alias means no call sites change.) `__all__` already lists `ExecutionPolicy`; the re-import preserves `from composable_agents.execution.harness import ExecutionPolicy` for existing users (e2e test imports it this way).

- [ ] **Step 7: Run the new tests and the full suite**

Run: `python -m pytest tests/test_effects_extraction.py -v && python -m pytest`
Expected: new tests PASS; all 447 existing tests PASS (this task is a pure refactor — any behavior change is a bug).

- [ ] **Step 8: Gates + commit**

Run: `uv run mypy --strict composable_agents && ruff check composable_agents tests`

```bash
git add composable_agents/execution/effects.py composable_agents/execution/policy.py \
        composable_agents/execution/activities.py composable_agents/execution/harness.py \
        tests/test_effects_extraction.py
git commit -m "refactor(execution): extract backend-neutral effects + policy layers"
```

---

### Task 2: Durable timer leaf — `delay(seconds=...)`

A reserved native tool `__sleep__`, mirroring `__human_gate__` exactly: the DSL emits a `CallStep(NativeTool(SLEEP_TOOL))` with the duration carried on `Ann.timeout`; freeze synthesizes its contract without a snapshot entry; the interpreter special-cases it to `Env.sleep`. Contract is `READ`/`IDEMPOTENT` (side-effect-free), so unlike the human gate it is race-safe. Note for manifest authors (documented in Task 10): under a `tools:` allow-list section, `__sleep__` must be granted like any other tool — identical to the human-gate behavior today.

**Files:**
- Modify: `composable_agents/ir.py:28` (constant), `composable_agents/freeze.py:45,110-121` (contract + resolve case), `composable_agents/derived.py:187-198` area (combinator), `composable_agents/execution/interpreter.py` (Env protocol, `_eval_prim`, `InMemoryEnv`), `composable_agents/execution/harness.py` (`_TemporalEnv.sleep`), `composable_agents/__init__.py` (export)
- Test: `tests/test_delay.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_delay.py
"""The reserved __sleep__ leaf: authoring, freeze, and interpretation."""
from __future__ import annotations

import asyncio

import pytest

from composable_agents.derived import delay
from composable_agents.execution.interpreter import InMemoryEnv, interpret
from composable_agents.ir import CallStep, NativeTool, SLEEP_TOOL
from composable_agents.projection import InMemoryProjection, ProjectionEmitter


def _env(**kwargs):
    return InMemoryEnv({}, ProjectionEmitter(InMemoryProjection()), **kwargs)


def test_delay_emits_reserved_call_leaf():
    node = delay(seconds=30)
    assert isinstance(node.step, CallStep)
    assert node.step.tool == NativeTool(SLEEP_TOOL)
    assert node.ann is not None and node.ann.timeout == 30


def test_delay_rejects_nonpositive():
    with pytest.raises(ValueError):
        delay(seconds=0)


def test_interpreter_sleeps_and_passes_value_through():
    env = _env()
    result = asyncio.run(interpret(delay(seconds=7), {"v": 1}, env))
    assert result.value == {"v": 1}
    assert env.sleeps == [7]


def test_inmemory_env_custom_sleeper():
    waited = []

    async def sleeper(seconds):
        waited.append(seconds)

    env = _env(sleeper=sleeper)
    asyncio.run(interpret(delay(seconds=2), "x", env))
    assert waited == [2]


def test_freeze_resolves_sleep_without_snapshot():
    from composable_agents.freeze import McpSnapshot, freeze

    frozen = freeze(delay(seconds=5), McpSnapshot())
    [tool] = list(frozen.manifest.values())
    assert tool.ref == NativeTool(SLEEP_TOOL)
    assert tool.contract.effect.value == "read"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_delay.py -v`
Expected: FAIL — `ImportError: cannot import name 'SLEEP_TOOL'`

- [ ] **Step 3: Add the constant to `composable_agents/ir.py`**

Directly below `HUMAN_GATE_TOOL = "__human_gate__"` (line 28):

```python
# Reserved native tool: the harness turns a call to this into a durable timer
# (Temporal: workflow timer; DBOS: DBOS.sleep) rather than an HTTP request.
# The duration in seconds rides on the node's Ann.timeout.
SLEEP_TOOL = "__sleep__"
```

- [ ] **Step 4: Freeze support in `composable_agents/freeze.py`**

1. Add `SLEEP_TOOL` to the existing `from .ir import (...)` list (it currently imports `HUMAN_GATE_TOOL` at line 29).
2. Below `_HUMAN_GATE_CONTRACT` (line 45):

```python
# The reserved sleep tool is side-effect-free and replay-safe by construction.
_SLEEP_CONTRACT = ToolContract(effect=Effect.READ, idempotency=Idempotency.IDEMPOTENT)
```

3. In `_resolve` (line 105), immediately after the human-gate special case (lines 112-120), add the parallel case:

```python
    # Reserved sleep tool: synthetic, no snapshot lookup.
    if isinstance(ref, NativeTool) and ref.name == SLEEP_TOOL:
        return FrozenTool.create(
            ref=ref,
            input_schema={},
            contract=asserted_contract or _SLEEP_CONTRACT,
            output_schema=None,
            server_version=None,
            asserted=True,
        )
```

- [ ] **Step 5: The `delay` combinator in `composable_agents/derived.py`**

`derived.py` already imports `_nid`, `_node` from `.dsl` (line 25) and `HUMAN_GATE_TOOL` etc. from `.ir`; add `SLEEP_TOOL` to that `from .ir import (...)` list. Directly after `human_gate` (line 198):

```python
def delay(*, seconds: int) -> Node:
    """A leaf that durably pauses the flow, passing its input through unchanged.

    Emits a ``call`` to the reserved tool ``__sleep__``; each harness turns it
    into its engine's durable timer (Temporal timer / ``DBOS.sleep``) instead of
    an HTTP call. The duration rides on the annotation's timeout.
    """
    if seconds < 1:
        raise ValueError("delay seconds must be >= 1")
    return _node(op=Op.PRIM, id=_nid("delay"), ann=Ann(timeout_s=seconds),
                 step=CallStep(tool=NativeTool(SLEEP_TOOL)))
```

(`Ann`, `CallStep`, `NativeTool`, `Op` are already imported by derived.py.) Add `"delay"` to derived.py's `__all__` next to `"HUMAN_GATE_TOOL"` (line 46 area).

- [ ] **Step 6: Interpreter support in `composable_agents/execution/interpreter.py`**

1. Add `SLEEP_TOOL` to the `from ..ir import (...)` list (line 35).
2. In the `Env` protocol, after `human_gate` (line 123):

```python
    async def sleep(self, seconds: int, cid: str) -> None: ...
```

3. In `_eval_prim` (line 226), after the human-gate special case (lines 232-234):

```python
        # Reserved sleep tool becomes a durable timer, not an HTTP call.
        if step.tool.kind == "native" and getattr(step.tool, "name", None) == SLEEP_TOOL:
            seconds = node.ann.timeout if node.ann and node.ann.timeout is not None else 0
            await env.sleep(seconds, cid)
            return Result(value)
```

4. `InMemoryEnv`: add a `sleeper` keyword to `__init__` (after `gate`, line 503): `sleeper: Optional[Callable[[int], Awaitable[None]]] = None,` — store `self._sleeper = sleeper` and `self.sleeps: list[int] = []` in the body; add the method next to `human_gate` (line 592):

```python
    async def sleep(self, seconds: int, cid: str) -> None:
        self.sleeps.append(seconds)
        if self._sleeper is not None:
            await self._sleeper(seconds)
```

(`Awaitable` is already imported at line 29.)

- [ ] **Step 7: Temporal env support in `composable_agents/execution/harness.py`**

In `_TemporalEnv`, next to `human_gate` (line 420):

```python
    async def sleep(self, seconds: int, cid: str) -> None:
        # asyncio.sleep inside a Temporal workflow is a durable timer.
        await asyncio.sleep(seconds)
```

- [ ] **Step 8: Root export**

In `composable_agents/__init__.py`, in the `from .derived import (...)` block that already aliases `human_gate as human_gate` (line 74): add `delay as delay`. In `__all__`, add `"delay"` next to `"human_gate"` (line 219).

- [ ] **Step 9: Run tests + full suite + gates, then commit**

Run: `python -m pytest tests/test_delay.py -v && python -m pytest && uv run mypy --strict composable_agents && ruff check composable_agents tests`
Expected: all PASS. The golden corpus must be untouched (no existing flow uses `__sleep__`); if any golden test fails, you broke freeze for existing flows — stop and fix.

```bash
git add composable_agents/ir.py composable_agents/freeze.py composable_agents/derived.py \
        composable_agents/execution/interpreter.py composable_agents/execution/harness.py \
        composable_agents/__init__.py tests/test_delay.py
git commit -m "feat(core): delay() durable timer leaf via reserved __sleep__ tool"
```

---

### Task 3: Flow continuation (chaining)

A flow whose final value is `continue_with(next_input)` is re-dispatched with `next_input` as a fresh segment. On Temporal, `FlowWorkflow` does this via `continue_as_new` (carrying cumulative `call_counts` so `maxCalls` budgets span the whole chain). The generic `run_chained` helper drives chaining for in-memory runs and is reused by the DBOS runner in Task 8.

**Files:**
- Create: `composable_agents/continuation.py`
- Modify: `composable_agents/execution/harness.py` (FlowWorkflow + `_TemporalEnv.call_counts_snapshot`), `composable_agents/__init__.py` (exports)
- Test: `tests/test_continuation.py`, `tests/test_e2e_temporal_continuation.py`

- [ ] **Step 1: Write the failing pure-core tests**

```python
# tests/test_continuation.py
from __future__ import annotations

import asyncio

import pytest

from composable_agents.continuation import (
    CONTINUATION_KEY, continuation_value, continue_with, is_continuation, run_chained,
)
from composable_agents.errors import ComposableAgentsError


def test_sentinel_roundtrip():
    s = continue_with({"cursor": 10})
    assert is_continuation(s)
    assert continuation_value(s) == {"cursor": 10}
    assert s[CONTINUATION_KEY] == {"cursor": 10}


def test_plain_values_are_not_continuations():
    for v in (None, 0, "x", [], {"a": 1}, {"__continue___": 1}):
        assert not is_continuation(v)


def test_run_chained_follows_segments():
    async def segment(value):
        n = value["n"]
        return continue_with({"n": n + 1}) if n < 3 else {"done": n}

    out = asyncio.run(run_chained(segment, {"n": 0}))
    assert out == {"done": 3}


def test_run_chained_bounds_segments():
    async def forever(value):
        return continue_with(value)

    with pytest.raises(ComposableAgentsError, match="did not settle"):
        asyncio.run(run_chained(forever, {}, max_segments=5))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_continuation.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'composable_agents.continuation'`

- [ ] **Step 3: Create `composable_agents/continuation.py`** (pure core — must pass strict mypy)

```python
# composable_agents/continuation.py
"""Flow continuation: the chaining convention shared by every backend.

A flow signals "re-dispatch me with this input" by making its *final value*
``continue_with(next_input)``. The engine binding decides how a segment becomes
durable (Temporal: ``continue_as_new``; DBOS: a fresh workflow per segment);
this module only owns the sentinel and the generic driver. The sentinel is part
of the wire format: ``{"__continue__": <next input>}``, optionally enriched by
a backend with bookkeeping keys (which :func:`continuation_value` ignores).
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from .errors import ComposableAgentsError

CONTINUATION_KEY = "__continue__"


def continue_with(value: Any) -> dict[str, Any]:
    """Wrap ``value`` as a continuation: the flow ends, a new segment starts on it."""
    return {CONTINUATION_KEY: value}


def is_continuation(value: Any) -> bool:
    return isinstance(value, dict) and CONTINUATION_KEY in value


def continuation_value(value: dict[str, Any]) -> Any:
    return value[CONTINUATION_KEY]


async def run_chained(
    run_segment: Callable[[Any], Awaitable[Any]],
    input: Any,
    *,
    max_segments: int = 1000,
) -> Any:
    """Drive ``run_segment`` until it settles on a non-continuation value."""
    value = input
    for _ in range(max_segments):
        out = await run_segment(value)
        if not is_continuation(out):
            return out
        value = continuation_value(out)
    raise ComposableAgentsError(
        f"flow did not settle within {max_segments} segments"
    )
```

- [ ] **Step 4: Run pure tests to verify they pass**

Run: `python -m pytest tests/test_continuation.py -v`
Expected: PASS

- [ ] **Step 5: Temporal binding — continue-as-new in `FlowWorkflow`**

In `composable_agents/execution/harness.py`:

1. Inside the `with workflow.unsafe.imports_passed_through():` block add:

```python
    from ..continuation import continuation_value, is_continuation
```

2. Add a snapshot accessor to `_TemporalEnv` (after `charge_call`, line 303):

```python
    def call_counts_snapshot(self) -> dict[str, int]:
        return dict(self._call_counts)
```

3. In `FlowWorkflow.run`, replace the final `return result.value` (line 583) with:

```python
        if is_continuation(result.value):
            # Chain: same frozen flow, new input, cumulative call counts so
            # maxCalls budgets span the whole chain, truncated history.
            workflow.continue_as_new(
                FlowInput(
                    session_id=inp.session_id,
                    input=continuation_value(result.value),
                    flow_json=flow_json,
                    manifest_json=manifest_json,
                    pinned_pures=pinned_pures,
                    max_call_limits=max_call_limits,
                    call_counts=env.call_counts_snapshot(),
                    policy=inp.policy,
                )
            )
        return result.value
```

- [ ] **Step 6: Write the gated Temporal e2e test** (also covers Task 2's timer on Temporal)

```python
# tests/test_e2e_temporal_continuation.py
"""continue-as-new chaining + durable delay, on Temporal's time-skipping server."""
from __future__ import annotations

import asyncio
import uuid

import pytest

from composable_agents import HAVE_TEMPORAL

pytestmark = pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")

if HAVE_TEMPORAL:
    from temporalio.testing import WorkflowEnvironment

    from composable_agents import arr, freeze, register_pure, seq
    from composable_agents.continuation import continue_with
    from composable_agents.derived import delay
    from composable_agents.freeze import McpSnapshot
    from composable_agents.execution.harness import run_flow
    from composable_agents.execution.worker import build_worker
    from composable_agents.execution.activities import WorkerContext


def _bump_or_finish(value):
    n = value["n"]
    return continue_with({"n": n + 1}) if n < 2 else {"done": n}


register_pure("test.bump_or_finish", _bump_or_finish)


def test_flow_chains_and_sleeps():
    async def main():
        env = await WorkflowEnvironment.start_time_skipping()
        try:
            flow = seq(delay(seconds=300), arr("test.bump_or_finish"))
            frozen = freeze(flow, McpSnapshot())
            worker = build_worker(env.client, WorkerContext(), task_queue="cont-test")
            async with worker:
                out = await run_flow(
                    env.client,
                    frozen.flow.to_json(),
                    {h: t.to_json() for h, t in frozen.manifest.items()},
                    session_id=f"cont-{uuid.uuid4().hex[:8]}",
                    input={"n": 0},
                    task_queue="cont-test",
                )
            # Two continue-as-new chains (n=0 -> 1 -> 2), three 300s timers skipped.
            assert out == {"done": 2}
        finally:
            await env.shutdown()

    asyncio.run(main())
```

Note: `freeze(...)` returns the frozen artifact; if its attribute names differ (check `composable_agents/freeze.py` — the object returned by `freeze()` and how `tests/test_e2e_temporal.py` serializes `manifest`), match what `tests/test_e2e_temporal.py` does for `flow_json`/`manifest_json` exactly.

- [ ] **Step 7: Root exports**

In `composable_agents/__init__.py` add near the other pure-core re-exports:

```python
from .continuation import (
    continuation_value as continuation_value,
    continue_with as continue_with,
    is_continuation as is_continuation,
    run_chained as run_chained,
)
```

and add `"continue_with", "is_continuation", "continuation_value", "run_chained"` to `__all__`.

- [ ] **Step 8: Run everything + commit**

Run: `python -m pytest tests/test_continuation.py tests/test_e2e_temporal_continuation.py -v && python -m pytest && uv run mypy --strict composable_agents && ruff check composable_agents tests`
Expected: PASS (e2e skips if temporalio missing; it is present in the dev env).

```bash
git add composable_agents/continuation.py composable_agents/execution/harness.py \
        composable_agents/__init__.py tests/test_continuation.py \
        tests/test_e2e_temporal_continuation.py
git commit -m "feat(core+temporal): flow continuation sentinel with continue-as-new chaining"
```

---

### Task 4: Bounded fan-out — `ExecutionPolicy.max_parallel`

`par`/`map_n` currently fan out unbounded. Add `gather_bounded` (semaphore-gated gather, deterministic under Temporal's sandboxed asyncio) and a `max_parallel` knob on `ExecutionPolicy` + `InMemoryEnv`.

**Files:**
- Modify: `composable_agents/execution/interpreter.py` (helper + `InMemoryEnv`), `composable_agents/execution/policy.py` (field), `composable_agents/execution/harness.py` (`_TemporalEnv.gather`)
- Test: `tests/test_bounded_gather.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_bounded_gather.py
from __future__ import annotations

import asyncio


def test_gather_bounded_caps_concurrency():
    from composable_agents.execution.interpreter import gather_bounded

    state = {"now": 0, "peak": 0}

    async def job(i):
        state["now"] += 1
        state["peak"] = max(state["peak"], state["now"])
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        state["now"] -= 1
        return i

    out = asyncio.run(gather_bounded([job(i) for i in range(8)], max_parallel=2))
    assert out == list(range(8))           # order preserved
    assert state["peak"] <= 2              # ceiling enforced


def test_gather_bounded_none_is_unbounded():
    from composable_agents.execution.interpreter import gather_bounded

    async def job(i):
        return i * 2

    out = asyncio.run(gather_bounded([job(i) for i in range(4)], max_parallel=None))
    assert out == [0, 2, 4, 6]


def test_policy_roundtrips_max_parallel():
    from composable_agents.execution.policy import ExecutionPolicy

    p = ExecutionPolicy(max_parallel=4)
    assert ExecutionPolicy.from_json(p.to_json()).max_parallel == 4
    assert ExecutionPolicy.from_json({}).max_parallel is None


def test_inmemory_env_accepts_max_parallel():
    from composable_agents.execution.interpreter import InMemoryEnv
    from composable_agents.projection import InMemoryProjection, ProjectionEmitter

    env = InMemoryEnv({}, ProjectionEmitter(InMemoryProjection()), max_parallel=3)
    assert env.max_parallel == 3
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_bounded_gather.py -v`
Expected: FAIL — `ImportError: cannot import name 'gather_bounded'`

- [ ] **Step 3: Implement `gather_bounded` in `interpreter.py`**

Place after `race_first_from_thunks` (line 477):

```python
async def gather_bounded(
    coros: Sequence[Awaitable[Any]],
    *,
    max_parallel: Optional[int],
) -> list[Any]:
    """``asyncio.gather`` with an optional concurrency ceiling.

    ``None`` (or a non-positive value) means unbounded — the existing behavior.
    A semaphore is replay-deterministic under Temporal's sandboxed event loop,
    so both engine envs share this helper.
    """
    items = list(coros)
    if max_parallel is None or max_parallel <= 0 or len(items) <= max_parallel:
        return list(await asyncio.gather(*items))

    sem = asyncio.Semaphore(max_parallel)

    async def gated(coro: Awaitable[Any]) -> Any:
        async with sem:
            return await coro

    return list(await asyncio.gather(*(gated(c) for c in items)))
```

- [ ] **Step 4: Wire `InMemoryEnv`**

Add `max_parallel: Optional[int] = None,` to `InMemoryEnv.__init__` (after `sleeper` from Task 2), store `self.max_parallel = max_parallel`, and change `InMemoryEnv.gather` (line 596) to:

```python
    async def gather(self, coros: Sequence[Awaitable[Any]]) -> list[Any]:
        return await gather_bounded(coros, max_parallel=self.max_parallel)
```

(Drop the now-redundant local `import asyncio` inside the method.)

- [ ] **Step 5: Wire `ExecutionPolicy` and `_TemporalEnv`**

In `composable_agents/execution/policy.py` add the field `max_parallel: Optional[int] = None` to `ExecutionPolicy`; in `to_json` add `"maxParallel": self.max_parallel` only when not None (match the style of the other optional-less fields — they always serialize, so serialize it always as `"maxParallel": self.max_parallel`); in `from_json` add `max_parallel=d.get("maxParallel", base.max_parallel),`.

In `harness.py`, `_TemporalEnv.gather` (line 424) becomes:

```python
    async def gather(self, coros: Sequence[Awaitable[Any]]) -> list[Any]:
        return await gather_bounded(coros, max_parallel=self._policy.max_parallel)
```

and add `gather_bounded` to the `from .interpreter import (...)` list inside the passed-through imports block.

- [ ] **Step 6: Run everything + commit**

Run: `python -m pytest tests/test_bounded_gather.py -v && python -m pytest && uv run mypy --strict composable_agents && ruff check composable_agents tests`
Expected: PASS.

```bash
git add composable_agents/execution/interpreter.py composable_agents/execution/policy.py \
        composable_agents/execution/harness.py tests/test_bounded_gather.py
git commit -m "feat(execution): bounded par fan-out via ExecutionPolicy.max_parallel"
```

---

### Task 5: Projection sink seam — `ProjectionSink` + `TeeStore`

The DBOS env runs outside any deterministic sandbox, so it can emit projection events straight to an external sink (mem-mcp will plug Logfire/Langfuse adapters in here). The framework piece is tiny: a sink protocol (append-only) and a tee store that satisfies `ProjectionStore`.

**Files:**
- Modify: `composable_agents/projection.py`
- Test: `tests/test_projection_tee.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_projection_tee.py
from __future__ import annotations

from composable_agents.projection import (
    InMemoryProjection, ProjectionEmitter, TeeStore,
)


class _ListSink:
    def __init__(self):
        self.events = []

    def append(self, event):
        self.events.append(event)


def test_tee_fans_out_and_queries_primary():
    primary = InMemoryProjection()
    sink = _ListSink()
    tee = TeeStore(primary, sink)

    emitter = ProjectionEmitter(tee)
    eid = emitter.plan("n1", "n1@1")
    emitter.did("n1", "n1@1", value={"x": 1}, causes=(eid,))

    assert [e.type.value for e in primary.events()] == ["Planned", "Did"]
    assert [e.type.value for e in sink.events] == ["Planned", "Did"]
    assert tee.events() == primary.events()


def test_tee_exposes_primary_value_store():
    primary = InMemoryProjection()
    tee = TeeStore(primary, _ListSink())
    # ProjectionEmitter discovers the value store via getattr(store, "values").
    assert tee.values is primary.values

    emitter = ProjectionEmitter(tee)
    emitter.did("n1", "n1@1", value={"big": "payload"})
    [did] = [e for e in primary.events() if e.type.value == "Did"]
    assert did.value_ref is not None
    assert primary.values.get(did.value_ref) == {"big": "payload"}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_projection_tee.py -v`
Expected: FAIL — `ImportError: cannot import name 'TeeStore'`

- [ ] **Step 3: Implement in `composable_agents/projection.py`**

After the `ProjectionStore` protocol definition (line ~110), add:

```python
class ProjectionSink(Protocol):
    """A write-only consumer of projection events (observability adapters)."""

    def append(self, event: ProjectionEvent) -> None: ...


class TeeStore:
    """A :class:`ProjectionStore` that fans every append out to extra sinks.

    Queries (``events``) are served by the primary store; sinks are
    fire-and-forget appenders (a Logfire exporter, a metrics counter). A sink
    exception propagates — a broken observability pipe should fail loudly in
    dev; production adapters are expected to catch their own transport errors.
    """

    def __init__(self, primary: "InMemoryProjection", *sinks: ProjectionSink) -> None:
        self._primary = primary
        self._sinks = tuple(sinks)
        # ProjectionEmitter discovers a value store via getattr(store, "values").
        self.values = primary.values

    def append(self, event: ProjectionEvent) -> None:
        self._primary.append(event)
        for sink in self._sinks:
            sink.append(event)

    def events(self) -> list[ProjectionEvent]:
        return self._primary.events()
```

Add `"ProjectionSink"` and `"TeeStore"` to projection.py's `__all__` if it has one (check the bottom of the file; if there is no `__all__`, skip).

- [ ] **Step 4: Run everything + commit**

Run: `python -m pytest tests/test_projection_tee.py -v && python -m pytest && uv run mypy --strict composable_agents && ruff check composable_agents tests`
Expected: PASS.

```bash
git add composable_agents/projection.py tests/test_projection_tee.py
git commit -m "feat(projection): ProjectionSink protocol + TeeStore fan-out"
```

---

### Task 6: DBOS dev environment + API conformance spike

Before building the backend, pin down the exact dbos-2.18 APIs the backend relies on. The spike is a permanent gated test — it doubles as an early-warning canary when dbos is upgraded.

**Files:**
- Modify: `pyproject.toml`
- Test: `tests/test_dbos_api_spike.py`

- [ ] **Step 1: Add the extra + dev dependency**

In `pyproject.toml` under `[project.optional-dependencies]`, after the `temporal` line:

```toml
# Durable execution on DBOS (steps, flow workflow, chaining runner).
# dbos requires Python >=3.11; the marker keeps the extra resolvable on 3.10,
# where importing the backend raises a clear ImportError instead.
dbos = ["dbos>=2.18; python_version >= '3.11'"]
```

and append `"dbos>=2.18; python_version >= '3.11'",` to the `dev` list.

- [ ] **Step 2: Provision the test database (one-time, local)**

```bash
docker run -d --name ca-dbos-pg -e POSTGRES_PASSWORD=ca -p 5433:5432 postgres:16
export DBOS_TEST_DATABASE_URL='postgresql://postgres:ca@localhost:5433/postgres'
uv sync --extra dev
```

(Document in the test module docstring; CI gets the same via a Postgres service container — CI wiring is out of scope here.)

- [ ] **Step 3: Write the spike test**

```python
# tests/test_dbos_api_spike.py
"""dbos-2.18 API conformance: every dbos API the backend uses, exercised raw.

Needs: ``pip install 'composable-agents[dbos]'`` and a Postgres reachable via
``DBOS_TEST_DATABASE_URL`` (see docker one-liner in the plan / deploy-dbos.md).
Skipped otherwise. If this file fails after a dbos upgrade, fix
``dbos_backend.py`` to match before anything else.
"""
from __future__ import annotations

import asyncio
import os
import uuid

import pytest

from composable_agents.execution import HAVE_DBOS

DB_URL = os.environ.get("DBOS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not HAVE_DBOS or not DB_URL,
    reason="dbos not installed or DBOS_TEST_DATABASE_URL not set",
)

if HAVE_DBOS and DB_URL:
    from dbos import DBOS, DBOSConfig, Queue, SetWorkflowID

    spike_queue = Queue("ca_spike", concurrency=2)

    @DBOS.step(retries_allowed=True, max_attempts=3)
    async def double(x: int) -> int:
        return x * 2

    @DBOS.workflow()
    async def spike_gather(xs: list[int]) -> list[int]:
        # Concurrent steps from one async workflow must be supported.
        return list(await asyncio.gather(*(double(x) for x in xs)))

    @DBOS.workflow()
    async def spike_sleep_recv(timeout_s: float) -> dict:
        await DBOS.sleep_async(0.1)
        msg = await DBOS.recv_async(topic="spike", timeout_seconds=timeout_s)
        return {"msg": msg}


@pytest.fixture(scope="module")
def dbos_runtime():
    DBOS(config=DBOSConfig(
        name=f"ca-spike-{uuid.uuid4().hex[:8]}",
        system_database_url=DB_URL,
    ))
    DBOS.launch()
    yield
    DBOS.destroy()


def test_async_workflow_with_concurrent_steps(dbos_runtime):
    async def main():
        with SetWorkflowID(f"spike-gather-{uuid.uuid4().hex[:8]}"):
            handle = await DBOS.start_workflow_async(spike_gather, [1, 2, 3, 4])
        return await handle.get_result()

    assert asyncio.run(main()) == [2, 4, 6, 8]


def test_sleep_send_recv(dbos_runtime):
    async def main():
        wfid = f"spike-recv-{uuid.uuid4().hex[:8]}"
        with SetWorkflowID(wfid):
            handle = await DBOS.start_workflow_async(spike_sleep_recv, 10.0)
        await asyncio.sleep(0.5)
        await DBOS.send_async(wfid, {"ok": True}, topic="spike")
        return await handle.get_result()

    assert asyncio.run(main()) == {"msg": {"ok": True}}


def test_recv_times_out_to_none(dbos_runtime):
    async def main():
        with SetWorkflowID(f"spike-timeout-{uuid.uuid4().hex[:8]}"):
            handle = await DBOS.start_workflow_async(spike_sleep_recv, 1.0)
        return await handle.get_result()

    assert asyncio.run(main()) == {"msg": None}


def test_queue_enqueue(dbos_runtime):
    async def main():
        with SetWorkflowID(f"spike-q-{uuid.uuid4().hex[:8]}"):
            handle = await spike_queue.enqueue_async(spike_gather, [5])
        return await handle.get_result()

    assert asyncio.run(main()) == [10]
```

**Note for the implementer:** `HAVE_DBOS` does not exist until this step — add it now (it is needed by every later task anyway). In `composable_agents/execution/__init__.py`, next to `HAVE_TEMPORAL` (line 24):

```python
HAVE_DBOS = find_spec("dbos") is not None
```

and append `"HAVE_DBOS"` to that module's `__all__` list.

- [ ] **Step 4: Run the spike**

Run: `python -m pytest tests/test_dbos_api_spike.py -v`
Expected: 4 PASS (with the env var set). **If any test fails on an API-name mismatch** (e.g. `sleep_async`/`recv_async`/`start_workflow_async`/`enqueue_async` spelled differently in dbos 2.18, or `DBOSConfig` not accepting `system_database_url`): consult `python -c "from dbos import DBOS; print([m for m in dir(DBOS) if not m.startswith('_')])"` and the dbos 2.18 docs, fix the spike to the real names, and **record the corrected names in a comment at the top of the spike file** — Tasks 7-9 must use whatever the spike establishes.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml composable_agents/execution/__init__.py tests/test_dbos_api_spike.py
git commit -m "test(dbos): API conformance spike + dbos extra"
```

---### Task 7: DBOS backend — steps, `DbosEnv`, `flow_workflow`

The core backend module. Design points: (a) effect steps are module-level `@DBOS.step`s delegating to `effects.py`; (b) DBOS retries any raised exception when `retries_allowed=True`, so settled policy decisions (`CapabilityDenied` etc.) are smuggled out as a return envelope and re-raised by the env — never retried; (c) retry shaping is quantized to two step variants (idempotent=5 attempts, write=3) because DBOS fixes retry config at decoration time; (d) reasoner steps never retry — on this backend, LLM resilience belongs to the injected `LlmCaller` (mem-mcp's `retry_policy.py`); (e) race/hedge/quorum and `app` nodes are rejected by a pre-dispatch IR scan.

**Files:**
- Modify: `composable_agents/errors.py` (`UnsupportedShapeError`)
- Create: `composable_agents/execution/dbos_backend.py`
- Modify: `composable_agents/execution/__init__.py` (lazy exports)
- Test: `tests/test_dbos_pure.py`

- [ ] **Step 1: Write the failing no-database tests**

```python
# tests/test_dbos_pure.py
"""DBOS-backend logic that needs no database: shape scan, error envelope,
retry-variant choice. Needs dbos importable (decorators at module import)."""
from __future__ import annotations

import pytest

from composable_agents.execution import HAVE_DBOS

pytestmark = pytest.mark.skipif(not HAVE_DBOS, reason="dbos not installed")

if HAVE_DBOS:
    from composable_agents import call, seq, think
    from composable_agents.derived import delay, race
    from composable_agents.dsl import app
    from composable_agents.errors import CapabilityDenied, UnsupportedShapeError
    from composable_agents.execution.dbos_backend import (
        assert_dbos_executable, decode_policy_error, encode_policy_error,
    )


def test_scan_accepts_pipeline_shapes():
    flow = seq(call("kb/search"), seq(think("triage"), delay(seconds=5)))
    assert_dbos_executable(flow)  # no raise


def test_scan_rejects_race():
    flow = race(call("kb/a"), call("kb/b"))
    with pytest.raises(UnsupportedShapeError, match="race"):
        assert_dbos_executable(flow)


def test_scan_rejects_app():
    flow = app("triage_controller")
    with pytest.raises(UnsupportedShapeError, match="app"):
        assert_dbos_executable(flow)


def test_policy_error_envelope_roundtrip():
    env = encode_policy_error(CapabilityDenied("tool 'x' exceeded maxCalls=2"))
    with pytest.raises(CapabilityDenied, match="maxCalls=2"):
        decode_policy_error(env)


def test_decode_passes_plain_values_through():
    assert decode_policy_error({"hits": 3}) == {"hits": 3}
    assert decode_policy_error(None) is None
    assert decode_policy_error([1, 2]) == [1, 2]
```

Note: `app` may not be exported at the package root — check `composable_agents/__init__.py`; the import line above pulls it from `composable_agents.dsl`, which is where it is defined. If `race` raises at *authoring* time without a manifest, build the race via `par`+`Merge(kind="race")` the way `tests/` already do (grep `kind=\"race\"` in tests/ and copy that construction).

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_dbos_pure.py -v`
Expected: FAIL — `ImportError: cannot import name 'UnsupportedShapeError'`

- [ ] **Step 3: Add `UnsupportedShapeError` to `composable_agents/errors.py`**

After `RaceAllFailed` (line 36):

```python
class UnsupportedShapeError(ComposableAgentsError):
    """The flow uses an operator this execution backend cannot run.

    Raised at dispatch time (pre-execution IR scan), never mid-run: a flow that
    starts on a backend always finishes there or fails for a different reason.
    """
```

- [ ] **Step 4: Create `composable_agents/execution/dbos_backend.py`**

```python
# composable_agents/execution/dbos_backend.py
"""The DBOS execution backend: frozen IR on dbos-transact durable workflows.

Mirrors :mod:`composable_agents.execution.harness` for DBOS. One workflow
(``flow_workflow``) interprets a frozen flow; every effect leaf is a
``@DBOS.step`` delegating to the backend-neutral :mod:`.effects` layer, so a
worker configured via :func:`composable_agents.execution.effects.configure`
serves both backends identically.

Backend-specific contracts (the deltas vs Temporal — see docs/deploy-dbos.md):

* **No race/hedge/quorum, no app nodes** (v1). DBOS cannot cancel an in-flight
  step, so racing semantics would lie. :func:`assert_dbos_executable` rejects
  these at dispatch; the compiled output of an ``eval_plan`` is re-scanned too.
* **Reasoner steps never retry.** LLM resilience belongs to the injected
  ``LlmCaller`` (the consumer's retry/fallback stack), not to a second,
  blind retry layer here. Tools keep contract-derived retries, quantized to
  two variants (idempotent: 5 attempts, write: 3) because DBOS fixes retry
  config at decoration time.
* **Policy errors are never retried.** A settled decision (CapabilityDenied,
  PlanRejected, ValidationError, FreezeError, PureDriftError) is returned from
  the step as an envelope and re-raised by the env.
* **Sub-flows run inline** in the parent workflow (their steps checkpoint into
  the parent's history). Temporal uses child workflows; DBOS v1 trades that
  isolation for simplicity.
* **Chaining** = one DBOS workflow per segment (see run_flow_dbos, Task 8);
  ``maxCalls`` budgets carry across segments via the continuation envelope.

Triggering (schedules, debounce, dedup ids, queue routing) stays OUTSIDE the
IR — that is the dispatch boundary (docs/dispatch-boundary.md). This module
deliberately exposes ``queue=`` pass-throughs and nothing more.
"""

from __future__ import annotations

import asyncio
from typing import Any, Optional, Sequence

from dbos import DBOS, Queue, SetWorkflowID  # noqa: F401 (Queue re-exported for callers)

from .. import agent_loop as al
from ..continuation import CONTINUATION_KEY, continuation_value, is_continuation
from ..contracts import manifest_from_json
from ..errors import (
    CapabilityDenied,
    ComposableAgentsError,
    FreezeError,
    PlanRejected,
    PureDriftError,
    UnsupportedShapeError,
    ValidationError,
)
from ..ir import Node
from ..kinds import Op
from ..projection import InMemoryProjection, ProjectionEmitter, ProjectionSink, TeeStore
from . import effects
from .effects import (
    CallToolInput,
    CompilePlanInput,
    InvokeReasonerInput,
    toolref_json_from_key,
)
from .interpreter import (
    BranchThunk,
    Result,
    call_contract,
    call_ref_key,
    gather_bounded,
    interpret,
)
from .policy import ExecutionPolicy

# recv() needs *some* timeout; a week is "effectively forever" for a gate while
# still letting an abandoned workflow drain. Override per node via ann.timeout.
_GATE_DEFAULT_TIMEOUT_S = 7 * 24 * 3600

_POLICY_ERRORS = (CapabilityDenied, PlanRejected, ValidationError, FreezeError, PureDriftError)
_POLICY_ERROR_KEY = "__ca_policy_error__"
_POLICY_ERROR_TYPES = {e.__name__: e for e in _POLICY_ERRORS}


# --------------------------------------------------------------------------- #
# Policy-error envelope: settled decisions must cross the step boundary as
# values so DBOS's retry machinery never sees them as failures.
# --------------------------------------------------------------------------- #
def encode_policy_error(exc: Exception) -> dict[str, Any]:
    return {_POLICY_ERROR_KEY: {"type": type(exc).__name__, "message": str(exc)}}


def decode_policy_error(out: Any) -> Any:
    if isinstance(out, dict) and _POLICY_ERROR_KEY in out:
        payload = out[_POLICY_ERROR_KEY]
        exc_type = _POLICY_ERROR_TYPES.get(payload.get("type"), ComposableAgentsError)
        raise exc_type(payload.get("message", "policy error"))
    return out


# --------------------------------------------------------------------------- #
# Pre-dispatch shape scan.
# --------------------------------------------------------------------------- #
def assert_dbos_executable(flow: Node) -> None:
    """Reject IR the DBOS backend cannot run (race family, app nodes)."""
    for n in flow.walk():
        if n.op == Op.PAR and n.merge is not None and n.merge.kind in {"race", "hedge", "quorum"}:
            raise UnsupportedShapeError(
                f"node {n.id!r}: merge kind {n.merge.kind!r} (race family) needs branch "
                "cancellation, which DBOS does not provide; run this flow on the "
                "Temporal backend or restructure with par/alt"
            )
        if n.op == Op.APP:
            raise UnsupportedShapeError(
                f"node {n.id!r}: app (agent-loop) nodes are not yet supported on the "
                "DBOS backend; run this flow on the Temporal backend"
            )


# --------------------------------------------------------------------------- #
# Projection sink (process-global, like effects.configure).
# --------------------------------------------------------------------------- #
_PROJECTION_SINK: Optional[ProjectionSink] = None


def set_projection_sink(sink: Optional[ProjectionSink]) -> None:
    """Install a process-wide sink that receives every projection event."""
    global _PROJECTION_SINK
    _PROJECTION_SINK = sink


# --------------------------------------------------------------------------- #
# Effect steps. Names are stable identifiers in DBOS's workflow_status table.
# --------------------------------------------------------------------------- #
@DBOS.step(retries_allowed=True, max_attempts=5)
async def callToolIdempotent(inp: dict) -> Any:
    try:
        return await effects.callTool(_call_tool_input(inp))
    except _POLICY_ERRORS as exc:
        return encode_policy_error(exc)


@DBOS.step(retries_allowed=True, max_attempts=3)
async def callToolWrite(inp: dict) -> Any:
    try:
        return await effects.callTool(_call_tool_input(inp))
    except _POLICY_ERRORS as exc:
        return encode_policy_error(exc)


@DBOS.step(retries_allowed=False)
async def invokeReasonerStep(inp: dict) -> Any:
    try:
        return await effects.invokeReasoner(
            InvokeReasonerInput(reasoner=inp["reasoner"], value=inp["value"], cid=inp["cid"])
        )
    except _POLICY_ERRORS as exc:
        return encode_policy_error(exc)


@DBOS.step(retries_allowed=False)
async def compilePlanStep(inp: dict) -> Any:
    try:
        return await effects.compilePlan(
            CompilePlanInput(
                planner=inp["planner"], value=inp["value"], cid=inp["cid"],
                manifest=inp.get("manifest"),
            )
        )
    except _POLICY_ERRORS as exc:
        return encode_policy_error(exc)


@DBOS.step(retries_allowed=False)
async def verifyPuresStep(pinned: dict) -> Any:
    try:
        await effects.verifyPures(pinned)
        return None
    except _POLICY_ERRORS as exc:
        return encode_policy_error(exc)


@DBOS.step(retries_allowed=True, max_attempts=3)
async def resolveSubflowStep(ref: str) -> dict:
    return await effects.resolveSubflow(ref)


@DBOS.step(retries_allowed=False)
async def resolveRuntimeCapabilitiesStep() -> dict:
    return await effects.resolveRuntimeCapabilities()


def _call_tool_input(inp: dict) -> CallToolInput:
    return CallToolInput(
        tool_ref=inp["tool_ref"], value=inp["value"], cid=inp["cid"],
        cache=inp.get("cache"),
    )


# --------------------------------------------------------------------------- #
# The Env.
# --------------------------------------------------------------------------- #
class DbosEnv:
    """An :class:`~composable_agents.execution.interpreter.Env` whose effects
    are DBOS steps. Lives entirely inside one ``flow_workflow`` execution."""

    def __init__(
        self,
        manifest,
        emitter: ProjectionEmitter,
        *,
        session_id: str,
        manifest_json: Optional[dict[str, Any]],
        policy: ExecutionPolicy,
        max_call_limits: Optional[dict[str, int]] = None,
        call_counts: Optional[dict[str, int]] = None,
    ) -> None:
        self.manifest = manifest
        self.emitter = emitter
        self._session = session_id
        self._manifest_json = manifest_json
        self._policy = policy
        self._max_call_limits = dict(max_call_limits or {})
        self._call_counts: dict[str, int] = dict(call_counts or {})
        self._cid = 0

    # --- identity / pures --- #
    def next_cid(self, node_id: str) -> str:
        self._cid += 1
        # Session-prefixed (unlike Temporal) because inline sub-flows share one
        # workflow: the prefix keeps Idempotency-Keys distinct across parent/child.
        return f"{self._session}/{node_id}@{self._cid}"

    def get_pure(self, name: str):
        from ..purity import get_pure as _gp

        return _gp(name)

    def charge_call(self, tool_key: str) -> None:
        limit = self._max_call_limits.get(tool_key)
        if limit is None:
            return
        count = self._call_counts.get(tool_key, 0)
        if count >= limit:
            raise CapabilityDenied(f"tool {tool_key!r} exceeded maxCalls={limit}")
        self._call_counts[tool_key] = count + 1

    def call_counts_snapshot(self) -> dict[str, int]:
        return dict(self._call_counts)

    # --- effect handlers --- #
    async def run_call(self, node: Node, value: Any, cid: str) -> Any:
        ref_key = call_ref_key(node, self.manifest)
        contract = call_contract(node, self.manifest)
        attempts = al.retry_max_attempts_for_contract(
            contract,
            idempotent_max_attempts=self._policy.idempotent_max_attempts,
            write_max_attempts=self._policy.write_max_attempts,
        )
        step = callToolIdempotent if attempts >= self._policy.idempotent_max_attempts else callToolWrite
        cache = node.ann.cache.to_json() if node.ann and node.ann.cache is not None else None
        out = await step({
            "tool_ref": toolref_json_from_key(ref_key),
            "value": value, "cid": cid, "cache": cache,
        })
        return decode_policy_error(out)

    async def invoke_reasoner(
        self, reasoner: str, value: Any, cid: str, timeout_s: Optional[int],
    ) -> Any:
        out = await invokeReasonerStep({"reasoner": reasoner, "value": value, "cid": cid})
        return decode_policy_error(out)

    async def compile_plan(self, planner: str, value: Any, cid: str) -> Node:
        out = await compilePlanStep({
            "planner": planner, "value": value, "cid": cid,
            "manifest": self._manifest_json,
        })
        plan = Node.from_json(decode_policy_error(out))
        assert_dbos_executable(plan)  # a compiled plan must obey backend limits too
        return plan

    async def run_sub(self, ref: str, contract, value: Any, cid: str) -> Any:
        resolved = await resolveSubflowStep(ref)
        child = Node.from_json(resolved["flowJson"])
        assert_dbos_executable(child)
        pinned = resolved.get("pinnedPures")
        if pinned:
            decode_policy_error(await verifyPuresStep(pinned))
        child_env = DbosEnv(
            manifest=manifest_from_json(resolved.get("manifestJson") or {}),
            emitter=self.emitter,
            session_id=f"{self._session}-sub-{cid}",
            manifest_json=resolved.get("manifestJson") or {},
            policy=self._policy,
            max_call_limits=self._max_call_limits,
            call_counts=dict(self._call_counts),
        )
        r: Result = await interpret(child, value, child_env)
        return r.value

    async def run_agent(
        self, controller: str, value: Any, cid: str,
        app_config: Optional[dict[str, Any]] = None,
    ) -> Any:
        raise UnsupportedShapeError(
            "app (agent-loop) nodes are not yet supported on the DBOS backend"
        )

    async def human_gate(self, value: Any, cid: str, timeout_s: Optional[int]) -> Any:
        payload = await DBOS.recv_async(
            topic=f"gate:{cid}",
            timeout_seconds=float(timeout_s) if timeout_s else float(_GATE_DEFAULT_TIMEOUT_S),
        )
        if payload is None:
            return {"approved": False, "reason": "timeout", "input": value}
        return payload

    async def sleep(self, seconds: int, cid: str) -> None:
        await DBOS.sleep_async(float(seconds))

    # --- concurrency --- #
    async def gather(self, coros: Sequence[Any]) -> list[Any]:
        return await gather_bounded(coros, max_parallel=self._policy.max_parallel)

    async def race_first(
        self, branches: Sequence[BranchThunk], *, kind: str, m: int, hedge_ms: Optional[int],
    ) -> Any:
        raise UnsupportedShapeError(
            f"merge kind {kind!r} (race family) is not supported on the DBOS backend"
        )


# --------------------------------------------------------------------------- #
# The workflow: one chain segment of one frozen flow.
# --------------------------------------------------------------------------- #
@DBOS.workflow(name="ca_flow")
async def flow_workflow(inp: dict) -> Any:
    """Interpret one segment. ``inp`` is a plain JSON dict (camelCase keys
    mirroring :class:`~composable_agents.execution.harness.FlowInput`)."""
    policy = ExecutionPolicy.from_json(inp.get("policy"))
    flow_json = inp.get("flowJson")
    manifest_json = inp.get("manifestJson") or {}

    if flow_json is None:
        if not inp.get("ref"):
            raise ValueError("flow_workflow input needs either flowJson or ref")
        resolved = await resolveSubflowStep(inp["ref"])
        flow_json = resolved["flowJson"]
        manifest_json = resolved.get("manifestJson") or {}
        if inp.get("pinnedPures") is None:
            inp = {**inp, "pinnedPures": resolved.get("pinnedPures")}

    pinned = inp.get("pinnedPures")
    if pinned is not None:
        decode_policy_error(await verifyPuresStep(pinned))

    max_call_limits = inp.get("maxCallLimits")
    if max_call_limits is None:
        caps = await resolveRuntimeCapabilitiesStep()
        max_call_limits = caps.get("maxCalls", {})

    flow = Node.from_json(flow_json)
    assert_dbos_executable(flow)

    store = InMemoryProjection()
    sink = _PROJECTION_SINK
    emitter = ProjectionEmitter(TeeStore(store, sink) if sink is not None else store)

    env = DbosEnv(
        manifest=manifest_from_json(manifest_json),
        emitter=emitter,
        session_id=inp["sessionId"],
        manifest_json=manifest_json,
        policy=policy,
        max_call_limits=max_call_limits,
        call_counts=inp.get("callCounts"),
    )
    result: Result = await interpret(flow, inp.get("input"), env)

    if is_continuation(result.value):
        # Enrich the sentinel so the runner can carry budgets into the next segment.
        return {
            CONTINUATION_KEY: continuation_value(result.value),
            "callCounts": env.call_counts_snapshot(),
        }
    return result.value
```

- [ ] **Step 5: Lazy exports in `composable_agents/execution/__init__.py`**

Add below the Temporal export tables (mirroring their pattern exactly):

```python
_DBOS_EXPORTS = [
    "DbosEnv",
    "assert_dbos_executable",
    "decode_policy_error",
    "encode_policy_error",
    "flow_workflow",
    "run_flow_dbos",
    "set_projection_sink",
    "submit_human_dbos",
]

_DBOS_ATTR_MODULES = {name: ".dbos_backend" for name in _DBOS_EXPORTS}
```

and extend `__getattr__`:

```python
def __getattr__(name: str) -> Any:
    module_name = _TEMPORAL_ATTR_MODULES.get(name)
    if module_name is not None:
        if not HAVE_TEMPORAL:
            raise AttributeError(name)
    else:
        module_name = _DBOS_ATTR_MODULES.get(name)
        if module_name is None:
            raise AttributeError(name)
        if not HAVE_DBOS:
            raise AttributeError(name)
    module = import_module(module_name, __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value
```

and change the `__all__` composition line to:

```python
__all__ = [
    # ... existing base list unchanged ...
] + (_TEMPORAL_EXPORTS if HAVE_TEMPORAL else []) + (_DBOS_EXPORTS if HAVE_DBOS else [])
```

(`run_flow_dbos`/`submit_human_dbos` land in Task 8 — the lazy table may name them now; the attr lookup only fires on use.)

- [ ] **Step 6: Run tests + gates + commit**

Run: `python -m pytest tests/test_dbos_pure.py -v && python -m pytest && uv run mypy --strict composable_agents && ruff check composable_agents tests`
Expected: PASS (dbos_backend is under the `composable_agents.execution.*` mypy exemption).

```bash
git add composable_agents/errors.py composable_agents/execution/dbos_backend.py \
        composable_agents/execution/__init__.py tests/test_dbos_pure.py
git commit -m "feat(dbos): DBOS backend core — effect steps, DbosEnv, ca_flow workflow"
```

---

### Task 8: DBOS runner — chaining, human-gate submit, root exports

**Files:**
- Modify: `composable_agents/execution/dbos_backend.py` (append), `composable_agents/__init__.py` (HAVE_DBOS)
- Test: covered by Task 9's e2e (the runner is IO-bound; its only pure logic — `run_chained` — was tested in Task 3)

- [ ] **Step 1: Append the runner + gate helper to `dbos_backend.py`**

```python
# --------------------------------------------------------------------------- #
# Client helpers.
# --------------------------------------------------------------------------- #
async def run_flow_dbos(
    flow_json: dict[str, Any],
    manifest_json: dict[str, Any],
    *,
    session_id: str,
    input: Any = None,
    policy: Optional[ExecutionPolicy] = None,
    pinned_pures: Optional[dict[str, str]] = None,
    max_call_limits: Optional[dict[str, int]] = None,
    queue: Optional[Queue] = None,
    max_segments: int = 1000,
) -> Any:
    """Run a frozen flow to settlement, following continuation segments.

    Segment ``i`` runs as workflow id ``session_id`` (i=0) /
    ``f"{session_id}-seg{i}"``, so a re-submission with the same session id is
    deduplicated by DBOS's one-execution-per-workflow-id guarantee, and a chain
    is inspectable in ``workflow_status`` by id prefix. Call this from inside a
    DBOS workflow for durable chaining (each enqueue checkpoints); from plain
    code, a crash between segments stalls the chain — the same contract as any
    other dispatch your process performs.
    """
    assert_dbos_executable(Node.from_json(flow_json))
    seg_input = input
    call_counts: Optional[dict[str, int]] = None
    for seg in range(max_segments):
        wfid = session_id if seg == 0 else f"{session_id}-seg{seg}"
        seg_payload = {
            "sessionId": wfid,
            "input": seg_input,
            "flowJson": flow_json,
            "manifestJson": manifest_json,
            "pinnedPures": pinned_pures,
            "maxCallLimits": max_call_limits,
            "callCounts": call_counts,
            "policy": (policy or ExecutionPolicy()).to_json(),
        }
        with SetWorkflowID(wfid):
            if queue is not None:
                handle = await queue.enqueue_async(flow_workflow, seg_payload)
            else:
                handle = await DBOS.start_workflow_async(flow_workflow, seg_payload)
        out = await handle.get_result()
        if not is_continuation(out):
            return out
        call_counts = out.get("callCounts") if isinstance(out, dict) else None
        seg_input = continuation_value(out)
    raise ComposableAgentsError(
        f"flow {session_id!r} did not settle within {max_segments} segments"
    )


async def submit_human_dbos(workflow_id: str, cid: str, value: Any) -> None:
    """Release a parked human gate in a running ``ca_flow`` workflow.

    ``cid`` is the gate's activation id; with the DBOS env's session-prefixed
    cids, the first gate of a root flow is ``f"{workflow_id}/{gate_node_id}@1"``.
    """
    await DBOS.send_async(workflow_id, value, topic=f"gate:{cid}")
```

- [ ] **Step 2: Root package export of `HAVE_DBOS`**

In `composable_agents/__init__.py`, extend the existing line 201 import:

```python
from .execution import (
    HAVE_TEMPORAL as HAVE_TEMPORAL,
    HAVE_DBOS as HAVE_DBOS,
)
```

and add `"HAVE_DBOS"` to `__all__` next to `"HAVE_TEMPORAL"` (line 251).

- [ ] **Step 3: Run gates + commit**

Run: `python -m pytest && uv run mypy --strict composable_agents && ruff check composable_agents tests`
Expected: PASS.

```bash
git add composable_agents/execution/dbos_backend.py composable_agents/__init__.py
git commit -m "feat(dbos): chaining runner, human-gate submit, HAVE_DBOS export"
```

---

### Task 9: DBOS end-to-end integration tests

Full flows on a real DBOS runtime: seq pipeline, durable timer, human gate (timeout + release), continuation chain with budget carry-over, bounded par. Same gating as the spike.

**Files:**
- Test: `tests/test_e2e_dbos.py`

- [ ] **Step 1: Write the e2e tests**

```python
# tests/test_e2e_dbos.py
"""End-to-end flows on a real DBOS runtime. Needs DBOS_TEST_DATABASE_URL
(see tests/test_dbos_api_spike.py for the docker one-liner)."""
from __future__ import annotations

import asyncio
import os
import time
import uuid

import pytest

from composable_agents.execution import HAVE_DBOS

DB_URL = os.environ.get("DBOS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not HAVE_DBOS or not DB_URL,
    reason="dbos not installed or DBOS_TEST_DATABASE_URL not set",
)

if HAVE_DBOS and DB_URL:
    from dbos import DBOS, DBOSConfig

    from composable_agents import arr, call, freeze, register_pure, seq
    from composable_agents.continuation import continue_with
    from composable_agents.derived import delay, human_gate
    from composable_agents.dsl import par
    from composable_agents.execution.dbos_backend import run_flow_dbos, submit_human_dbos
    from composable_agents.execution.effects import WorkerContext, configure
    from composable_agents.execution.policy import ExecutionPolicy
    from composable_agents.freeze import (
        McpServerSnapshot, McpSnapshot, McpToolSpec,
    )

    # Match how tests/test_e2e_temporal.py builds its snapshot + serializes the
    # frozen artifact; reuse its exact construction if the names below drift.
    SNAPSHOT = McpSnapshot(servers={
        "kb": McpServerSnapshot(version="1.0", tools={
            "search": McpToolSpec(input_schema={}),
        }),
    })

    def _frozen(flow):
        frozen = freeze(flow, SNAPSHOT)
        return frozen.flow.to_json(), {h: t.to_json() for h, t in frozen.manifest.items()}

    _CONC = {"now": 0, "peak": 0}

    async def fake_mcp(server, tool, value, key):
        _CONC["now"] += 1
        _CONC["peak"] = max(_CONC["peak"], _CONC["now"])
        await asyncio.sleep(0.05)
        _CONC["now"] -= 1
        return {"echo": value, "tool": f"{server}/{tool}"}

    def _bump(value):
        n = value["n"]
        return continue_with({"n": n + 1}) if n < 2 else {"done": n}

    register_pure("e2edbos.bump", _bump)


@pytest.fixture(scope="module")
def dbos_runtime():
    configure(WorkerContext(mcp_call=fake_mcp))
    DBOS(config=DBOSConfig(
        name=f"ca-e2e-{uuid.uuid4().hex[:8]}",
        system_database_url=DB_URL,
    ))
    DBOS.launch()
    yield
    DBOS.destroy()


def _run(coro):
    return asyncio.run(coro)


def test_seq_pipeline(dbos_runtime):
    flow_json, manifest_json = _frozen(seq(call("kb/search"), call("kb/search")))
    out = _run(run_flow_dbos(
        flow_json, manifest_json,
        session_id=f"e2e-seq-{uuid.uuid4().hex[:8]}", input={"q": "x"},
    ))
    assert out["tool"] == "kb/search"
    assert out["echo"]["tool"] == "kb/search"   # first call's output fed the second


def test_delay_is_durable_wait(dbos_runtime):
    flow_json, manifest_json = _frozen(delay(seconds=1))
    t0 = time.monotonic()
    out = _run(run_flow_dbos(
        flow_json, manifest_json,
        session_id=f"e2e-delay-{uuid.uuid4().hex[:8]}", input={"v": 9},
    ))
    assert out == {"v": 9}
    assert time.monotonic() - t0 >= 1.0


def test_human_gate_timeout(dbos_runtime):
    flow_json, manifest_json = _frozen(human_gate(timeout_s=1))
    out = _run(run_flow_dbos(
        flow_json, manifest_json,
        session_id=f"e2e-gate-to-{uuid.uuid4().hex[:8]}", input={"ask": 1},
    ))
    assert out == {"approved": False, "reason": "timeout", "input": {"ask": 1}}


def test_human_gate_release(dbos_runtime):
    gate = human_gate(timeout_s=30)
    flow_json, manifest_json = _frozen(gate)
    wfid = f"e2e-gate-{uuid.uuid4().hex[:8]}"

    async def main():
        task = asyncio.create_task(run_flow_dbos(
            flow_json, manifest_json, session_id=wfid, input={"ask": 1},
        ))
        await asyncio.sleep(1.0)
        # DbosEnv cids are session-prefixed; the root node is activation 1.
        await submit_human_dbos(wfid, f"{wfid}/{gate.id}@1", {"approved": True})
        return await task

    assert _run(main()) == {"approved": True}


def test_continuation_chain(dbos_runtime):
    flow_json, manifest_json = _frozen(arr("e2edbos.bump"))
    out = _run(run_flow_dbos(
        flow_json, manifest_json,
        session_id=f"e2e-chain-{uuid.uuid4().hex[:8]}", input={"n": 0},
    ))
    assert out == {"done": 2}


def test_bounded_par(dbos_runtime):
    _CONC["peak"] = 0
    flow_json, manifest_json = _frozen(
        par(call("kb/search"), call("kb/search"), call("kb/search"))
    )
    out = _run(run_flow_dbos(
        flow_json, manifest_json,
        session_id=f"e2e-par-{uuid.uuid4().hex[:8]}", input={"q": "x"},
        policy=ExecutionPolicy(max_parallel=1),
    ))
    assert len(out) == 3
    assert _CONC["peak"] == 1
```

Construction notes for the implementer (verify against existing code before running):
- `arr("e2edbos.bump")` must be a *frozen-flow-legal* leaf: check how `tests/` freeze flows containing `arr` (pinned pures). If `freeze` pins pure hashes, pass the resulting `pinnedPures` through `run_flow_dbos(pinned_pures=...)` exactly as `run_flow` does in the Temporal e2e.
- `McpSnapshot`/`McpServerSnapshot`/`McpToolSpec` constructor kwargs: copy the working construction from `tests/test_e2e_temporal.py` (lines ~38-44 import them; the instantiation is further down that file).
- `par(...)` arity: if `dsl.par` is binary, nest it (`par(a, par(b, c))`) — `_all_branches` flattens the chain, so the test's "3 branches" assertion holds either way.

- [ ] **Step 2: Run the e2e suite**

Run: `python -m pytest tests/test_e2e_dbos.py -v`
Expected: 6 PASS (with `DBOS_TEST_DATABASE_URL` set). Triage guide: failures in `test_seq_pipeline` → effects wiring; `test_delay_*` → `DBOS.sleep_async`; gate tests → recv/send topics or the cid prefix scheme; `test_continuation_chain` → segment payload keys; `test_bounded_par` → `gather_bounded` wiring in `DbosEnv.gather`.

- [ ] **Step 3: Full suite + gates + commit**

Run: `python -m pytest && uv run mypy --strict composable_agents && ruff check composable_agents tests`

```bash
git add tests/test_e2e_dbos.py
git commit -m "test(dbos): end-to-end flows — pipeline, timer, gates, chaining, bounded par"
```

---

### Task 10: Documentation — dispatch boundary, DBOS deploy guide, SPEC addendum

**Files:**
- Create: `docs/dispatch-boundary.md`, `docs/deploy-dbos.md`
- Modify: `docs/SPEC.md`, `README.md`

- [ ] **Step 1: Write `docs/dispatch-boundary.md`**

```markdown
# The Dispatch Boundary

A frozen flow describes **processing**: what happens to a value once work has
begun. Everything that decides **when and whether** work begins lives outside
the IR, in the *dispatch layer* — the thin code that tools an input to a
backend runner (`run_flow` on Temporal, `run_flow_dbos` on DBOS).

Outside the IR (dispatch-layer concerns):

| Concern | Why it stays outside | Where it lives |
|---|---|---|
| Schedules / cron | "When to start" is not part of the computation | Temporal Schedules, `@DBOS.scheduled`, your scheduler |
| Debounce / batching windows | Collapses *inputs* before any flow exists | `dbos.Debouncer`, signal-with-start patterns |
| Dedup / idempotent submission | Identity of a *run*, not of a step | Workflow ids (both engines dedupe per id) |
| Webhook / event triggers | Transport, auth, replay protection | Your HTTP layer |
| Queue/worker routing | Capacity management across replicas | Temporal task queues, DBOS queues + roles |

Inside the IR (processing concerns): sequencing, fan-out (`par`, bounded by
`ExecutionPolicy.max_parallel`), branching (`alt`), bounded loops
(`iter_up_to`), durable waits (`delay`, `human_gate`), staged plans, sub-flows,
budgets, and capability grants.

**Continuation sits exactly on the boundary.** A flow ends with
`continue_with(next_input)` to say "the processing of *this* segment is done;
dispatch me again with that input." The flow never schedules itself — the
runner does (`continue_as_new` on Temporal, a fresh workflow id per segment on
DBOS) — so segment dispatch stays inspectable, deduplicable, and cancelable by
the same machinery as any other dispatch.

This split is what makes frozen flows engine-portable: a flow re-authored from
tool-rolled orchestration must move *only its processing* into the IR. If you
find yourself wanting a cron expression, a debounce window, or a dedup key
inside a flow, you have found dispatch — keep it outside.
```

- [ ] **Step 2: Write `docs/deploy-dbos.md`**

```markdown
# Running flows on DBOS

The DBOS backend (`composable_agents.execution.dbos_backend`) runs frozen
flows on [dbos-transact](https://docs.dbos.dev) — durable workflows
checkpointed in your existing Postgres, no extra cluster.

## Install

    pip install 'composable-agents[dbos]'    # dbos>=2.18, Python >= 3.11

## Worker wiring

Effects are configured exactly like the Temporal worker — one process-global
`WorkerContext` — and the backend module must be imported **before**
`DBOS.launch()` (step registration happens at import):

```python
from dbos import DBOS, DBOSConfig
from composable_agents.execution.effects import WorkerContext, configure
import composable_agents.execution.dbos_backend as ca_dbos

configure(WorkerContext(mcp_call=my_mcp_caller, llm=my_llm_caller))
ca_dbos.set_projection_sink(my_logfire_sink)   # optional, see ProjectionSink

DBOS(config=DBOSConfig(name="my-app", system_database_url=DB_URL))
DBOS.launch()
```

## Running a flow

```python
from composable_agents.execution.dbos_backend import run_flow_dbos

result = await run_flow_dbos(
    flow_json, manifest_json,
    session_id="job-123",            # workflow id -> DBOS dedupes resubmission
    input={"q": "..."},
    queue=my_dbos_queue,             # optional: route to a DBOS queue/role
)
```

`run_flow_dbos` follows continuation segments (`continue_with`) as
`job-123`, `job-123-seg1`, `job-123-seg2`, … carrying `maxCalls` budgets across
the chain. Human gates park on `DBOS.recv`; release with
`submit_human_dbos(workflow_id, cid, value)`.

## Differences from the Temporal backend

| | Temporal | DBOS |
|---|---|---|
| race / hedge / quorum | supported | **rejected at dispatch** (no step cancellation) |
| `app` (agent loop) nodes | child `AgentWorkflow` | **rejected at dispatch** (v1) |
| Reasoner retries | engine retry (4 attempts) | **none — your `LlmCaller` owns resilience** |
| Tool retries | per-contract `RetryPolicy` | quantized: idempotent 5 / write 3 attempts |
| Sub-flows | child workflow | inline in the parent workflow |
| Chaining | `continue_as_new` | one workflow per segment |
| Projection | interceptor over history | in-env emit + `set_projection_sink` |

`assert_dbos_executable(flow)` runs the rejection scan; call it at deploy time
to fail before dispatch.
```

- [ ] **Step 3: SPEC + README touch-ups**

In `docs/SPEC.md`, append a short normative section (place it with the other reserved-tool / wire-format text; find the section that specifies `__human_gate__` and add alongside):

```markdown
### Reserved tool: `__sleep__`

A `call` to the reserved native tool `__sleep__` is a durable timer, not an
HTTP call. The duration in seconds rides on the node's `ann.timeout`. Freeze
resolves it synthetically (no snapshot entry) with an asserted
`read`/`idempotent` contract, so it is race-safe. Capability semantics match
`__human_gate__`: under a `tools:` allow-list it must be granted explicitly.

### Continuation (chaining) convention

A flow whose final value is `{"__continue__": <next input>}` requests
re-dispatch with that input as a fresh segment. Backends MUST run the next
segment under the same frozen flow + manifest and SHOULD carry cumulative
`maxCalls` counts across segments. Backends MAY enrich the sentinel object with
bookkeeping keys; consumers MUST read the next input only from `__continue__`.

### The dispatch boundary

Triggering (schedules, debounce, dedup ids, webhooks, queue routing) is not
representable in the IR by design. See docs/dispatch-boundary.md.
```

In `README.md`, add one line to wherever the docs are indexed (there is a docs list / links section): `- [Dispatch boundary](docs/dispatch-boundary.md) — what belongs in a flow vs. the dispatch layer` and `- [Deploy on DBOS](docs/deploy-dbos.md) — durable flows on Postgres via dbos-transact`.

- [ ] **Step 4: Commit**

```bash
git add docs/dispatch-boundary.md docs/deploy-dbos.md docs/SPEC.md README.md
git commit -m "docs: dispatch boundary, DBOS deploy guide, __sleep__ + continuation spec"
```

---

### Task 11: Final verification sweep

- [ ] **Step 1: Full matrix**

```bash
python -m pytest -v
uv run mypy --strict composable_agents
ruff check composable_agents tests
python -m pytest tests/test_dbos_api_spike.py tests/test_e2e_dbos.py -v   # with DBOS_TEST_DATABASE_URL set
python -m pytest tests/test_e2e_temporal.py tests/test_e2e_temporal_continuation.py -v
```

Expected: everything green; existing 447 tests + ~35 new ones.

- [ ] **Step 2: Golden corpus sanity**

Run the golden-corpus tests specifically (grep `tests/` for the golden/corpus test module and run it): the 10 reference flows' IR/manifest checksums must be byte-identical to before this plan — all changes were additive (new reserved tool, new policy field serialized only in new flows... note: if `ExecutionPolicy.to_json` is part of any golden snapshot, the new `maxParallel` key WILL change it; in that case serialize `maxParallel` only when not None and update the test in Task 4 accordingly).

- [ ] **Step 3: Smoke the import matrix**

```bash
python -c "import composable_agents; print(composable_agents.HAVE_TEMPORAL, composable_agents.HAVE_DBOS)"
python -m pytest tests/test_effects_extraction.py::test_effects_importable_without_temporalio -v
```

- [ ] **Step 4: Final commit (if any fixups) + wrap**

```bash
git add -A && git commit -m "chore: post-plan verification fixups" || echo "tree clean"
```

---

## Self-Review Notes (already applied)

- **Spec coverage:** DBOS Env backend → Tasks 6-9; durable timer → Task 2; FlowWorkflow chaining → Task 3; bounded fan-out → Task 4; projection sink → Task 5 (+ DBOS wiring in Task 7); dispatch-boundary spec → Task 10. The effects extraction (Task 1) is the enabling refactor.
- **Known uncertainty, made explicit:** exact dbos-2.18 API spellings (`sleep_async`, `recv_async`, `start_workflow_async`, `enqueue_async`, `DBOSConfig(system_database_url=...)`) are pinned by the Task 6 spike *before* the backend is written; Tasks 7-9 follow the spike's findings.
- **Known uncertainty, made explicit:** `freeze()` artifact attribute names and `McpSnapshot` constructors in test code are flagged to be copied from `tests/test_e2e_temporal.py` rather than trusted from this plan.
- **Type consistency:** `Env.sleep(seconds: int, cid: str)` is implemented by `InMemoryEnv` (Task 2 Step 6), `_TemporalEnv` (Task 2 Step 7), `DbosEnv` (Task 7 Step 4). `call_counts_snapshot()` exists on `_TemporalEnv` (Task 3) and `DbosEnv` (Task 7). `gather_bounded(coros, *, max_parallel)` is used by all three envs. `ExecutionPolicy` import path changes once (Task 1) and gains `max_parallel` once (Task 4).
