# WS1 — `ca` Pure-Registry Fix (validate/run in the child) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `ca lint` and `ca run` succeed for any flow that uses a `@pure` (including the canonical quickstart), by running `validate`/`interpret` in the child process that imported the user module — where the pure registry is live.

**Architecture:** Today the `ca` resolve child (`_resolve_child.py`) imports the user module (registering pures *in the child*) but emits only the IR JSON; the parent then runs `validate` (`lint.py`) and `interpret` (`runner.py`) in a process where no `@pure` decorator ever ran, so the pure registry is empty → `UNKNOWN_PURE`. We move `validate` and `interpret` **into the child** (mirroring the existing `freeze` action, which already calls `deploy()` in-child) and reduce the parent to a thin caller that renders child results. This is Approach B from the design spec (`docs/plans/2026-06-29-composable-agents-dx-improvements.md` §4.3); it guarantees `ca run` ≡ `dry_run` parity by construction.

**Tech Stack:** Python 3.12+, the `composable_agents.ca` package (Typer CLI), the in-memory interpreter (`composable_agents.execution.interpreter`), projection (`composable_agents.projection`), pytest.

## Global Constraints

- Python **3.12+**. (copied from spec / cheatsheet)
- The **pure core must not import `temporalio`**; only `composable_agents/execution/` may. `composable_agents/ca/` is allowed to import the interpreter/projection (it already does). Do not add a `temporalio` import anywhere in `ca/`.
- Verify gates, run **all three** and they must be clean before any commit that closes a task:
  - `python -m pytest tests/cli -q` (use `python -m pytest`, never bare `pytest`)
  - `uv run mypy --strict composable_agents`
  - `ruff check composable_agents`
- **Determinism contract is preserved**: pures stay registered by raw `@pure` source in the child; we are not changing how pures register, only *where* validate/interpret runs.
- Public APIs stay fully typed (the repo runs `mypy --strict` on the package, not tests).
- Keep the existing `resolve` (IR-only) child action and `resolve_agent` parent function intact — `ls`/`show`/`graph`/`deploy`/`status` depend on them.

## File Structure

- **Create** `composable_agents/ca/_echo.py` — the offline echo-env builder, extracted verbatim from `runner.py` so both `runner.py` and the resolve child can build the same dev env. One responsibility: turn a `Node` into an `InMemoryEnv` + its `InMemoryProjection`.
- **Modify** `composable_agents/ca/_resolve_child.py` — add `lint` and `run` actions that validate/interpret in-child and emit JSON.
- **Modify** `composable_agents/ca/resolve.py` — add a generic `_invoke_child(...)` and two parent wrappers `lint_agent(...)` / `run_agent(...)` returning small result dataclasses.
- **Modify** `composable_agents/ca/lint.py` — consume child-side diagnostics instead of validating in-parent.
- **Modify** `composable_agents/ca/runner.py` — `run_agent_local(...)` delegates to the child via `run_agent(...)`; keep `RunOutcome` (still used by the Temporal env path in `cli.run`); echo helpers now live in `_echo.py`.
- **Create** `tests/cli/test_pure_cli_regression.py` — the regression: `ca lint`/`ca run` over a flow that uses a `@pure`, both at the function level and through the real CLI entry point.

---

### Task 1: Extract the echo-env builder into `ca/_echo.py`

Pure refactor with no behavior change. Existing `tests/cli/test_run.py` is the safety net.

**Files:**
- Create: `composable_agents/ca/_echo.py`
- Modify: `composable_agents/ca/runner.py`
- Test: `tests/cli/test_run.py` (existing — must stay green)

**Interfaces:**
- Produces (consumed by Tasks 2 & 4):
  - `composable_agents.ca._echo.build_echo_env(node: Node) -> tuple[InMemoryEnv, InMemoryProjection]`
  - `composable_agents.ca._echo._echo`, `_echo_tools`, `_echo_reasoners`, `_echo_subs`, `_echo_agents`, `_clear_frozen_hashes` (moved verbatim from `runner.py`).

- [ ] **Step 1: Create `composable_agents/ca/_echo.py`** with the helpers moved out of `runner.py`, plus a `build_echo_env` that packages the env construction currently inline in `run_agent_local`:

```python
from __future__ import annotations

from typing import Any, Callable

from composable_agents.execution.interpreter import InMemoryEnv
from composable_agents.ir import CallStep, Node, SubStep, toolref_key
from composable_agents.kinds import EnforcementMode, Op
from composable_agents.projection import InMemoryProjection, ProjectionEmitter

EchoHandler = Callable[[Any], Any]


def _echo(value: Any) -> dict[str, Any]:
    """Dev stub: wrap any handler's input in a record so env folds stay happy."""
    return {"output": value}


def _clear_frozen_hashes(flow: Node) -> None:
    for node in flow.walk():
        step = node.step
        if isinstance(step, CallStep):
            step.frozen_hash = None


def _echo_tools(flow: Node) -> dict[str, EchoHandler]:
    tools: dict[str, EchoHandler] = {}
    for ref in flow.tool_refs():
        tools[toolref_key(ref)] = _echo
    return tools


def _echo_reasoners(flow: Node) -> dict[str, EchoHandler]:
    reasoners: dict[str, EchoHandler] = {}
    for node in flow.walk():
        step = node.step
        reasoner = getattr(step, "reasoner", None)
        if isinstance(reasoner, str):
            reasoners[reasoner] = _echo
        if node.op in {Op.APP, Op.EVAL_PLAN} and node.controller is not None:
            reasoners[node.controller] = _echo
    return reasoners


def _echo_subs(flow: Node) -> dict[str, EchoHandler]:
    subs: dict[str, EchoHandler] = {}
    for node in flow.walk():
        step = node.step
        if isinstance(step, SubStep):
            subs[step.ref] = _echo
    return subs


def _echo_agents(flow: Node) -> dict[str, EchoHandler]:
    agents: dict[str, EchoHandler] = {}
    for node in flow.walk():
        if node.op == Op.APP and node.controller is not None:
            agents[node.controller] = _echo
    return agents


def build_echo_env(node: Node) -> tuple[InMemoryEnv, InMemoryProjection]:
    """Build the offline dev env for a flow: record-returning stubs for every
    tool/reasoner/sub/agent, an auto-approving gate, dev-mode enforcement, and a
    fresh projection to capture events. Mutates ``node`` to clear frozen hashes."""
    _clear_frozen_hashes(node)
    projection = InMemoryProjection()
    env = InMemoryEnv(
        {},
        ProjectionEmitter(projection),
        tools=_echo_tools(node),
        reasoners=_echo_reasoners(node),
        subs=_echo_subs(node),
        agents=_echo_agents(node),
        gate=lambda value: {"approved": True, "input": value},
        mode=EnforcementMode.DEV,
    )
    return env, projection
```

- [ ] **Step 2: Rewrite `composable_agents/ca/runner.py` to import from `_echo`** and use `build_echo_env`. The file shrinks to `RunOutcome` + `run_agent_local` (still in-parent for now; Task 4 redirects it to the child):

```python
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from composable_agents.ca._echo import build_echo_env
from composable_agents.ca.resolve import ResolvedAgent
from composable_agents.execution.interpreter import interpret
from composable_agents.ir import Node
from composable_agents.projection import ProjectionEvent


@dataclass(frozen=True)
class RunOutcome:
    run_id: str
    value: Any
    events: list[ProjectionEvent] = field(default_factory=list)
    error: str | None = None


def run_agent_local(resolved: ResolvedAgent, value: Any, *, run_id: str) -> RunOutcome:
    if resolved.error is not None:
        return RunOutcome(run_id=run_id, value=None, events=[], error=resolved.error)
    projection = None
    try:
        node = Node.from_json(resolved.ir)
        env, projection = build_echo_env(node)
        result = asyncio.run(interpret(node, value, env))
    except Exception as exc:  # noqa: BLE001 - surface runtime errors in the outcome.
        events = projection.events() if projection is not None else []
        return RunOutcome(run_id=run_id, value=None, events=events, error=str(exc))
    return RunOutcome(run_id=run_id, value=result.value, events=projection.events(), error=None)
```

- [ ] **Step 3: Run the existing run tests to confirm no regression**

Run: `python -m pytest tests/cli/test_run.py -q`
Expected: PASS (same behavior as before the extraction).

- [ ] **Step 4: Run the gates**

Run: `ruff check composable_agents && uv run mypy --strict composable_agents`
Expected: clean.

- [ ] **Step 5: Commit**

```bash
git add composable_agents/ca/_echo.py composable_agents/ca/runner.py
git commit -m "refactor(ca): extract offline echo-env builder into ca/_echo"
```

---

### Task 2: Child-side `lint` action + parent `lint_agent`; rewire `lint.py`

**Files:**
- Modify: `composable_agents/ca/_resolve_child.py`
- Modify: `composable_agents/ca/resolve.py`
- Modify: `composable_agents/ca/lint.py`
- Test: `tests/cli/test_pure_cli_regression.py` (new)

**Interfaces:**
- Consumes: `_discover_agent(root, src, target) -> _DiscoveryResult` (existing in `_resolve_child.py`); `composable_agents.validate.validate(node) -> list[Diagnostic]`.
- Produces (consumed by `lint.py` and Task 3):
  - `composable_agents.ca.resolve.LintResolution(diagnostics: list[dict[str, str]], error: str | None)`
  - `composable_agents.ca.resolve.lint_agent(cfg: JulepConfig, name: str, *, timeout: float = 30.0) -> LintResolution`
  - `composable_agents.ca.resolve._invoke_child(cfg: JulepConfig, extra: dict[str, Any], *, timeout: float = 30.0) -> dict[str, Any]`

- [ ] **Step 1: Write the failing regression test (lint half)**

Create `tests/cli/test_pure_cli_regression.py`. The flow uses a `@pure` *and* an echo-tolerant pure body (does not index tool-output keys, so it cannot fail for an unrelated `KeyError`):

```python
# tests/cli/test_pure_cli_regression.py
from pathlib import Path

import pytest

# A flow that uses a @pure. The pure body is echo-tolerant: it reads only
# dict.keys(), so it never KeyErrors under ca run's {"output": value} echo stubs.
PURE_SAMPLE = '''
from composable_agents import flow, pure, think, tool

@tool(effect="read", idempotent=True)
def lookup(ticket: str) -> dict:
    return {"queue": "billing"}

@pure("passthrough")
def passthrough(hit: dict) -> dict:
    return {"seen": sorted(hit.keys())}

@flow
def triage(ticket: str) -> dict:
    hit = lookup(ticket)
    prompt = passthrough(hit)
    answer = think("reply", prompt)
    return prompt | answer
'''


@pytest.fixture
def pure_module(tmp_path: Path) -> Path:
    """A ca project whose only agent uses a @pure (the case the suite never covered)."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "agents.py").write_text(PURE_SAMPLE, encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text('[tool.julep]\nsrc = ["pkg"]\n', encoding="utf-8")
    return tmp_path


def test_lint_resolves_pures_no_unknown_pure(pure_module: Path) -> None:
    from composable_agents.ca.config import load_config
    from composable_agents.ca.lint import lint_agents

    cfg = load_config(pure_module)
    findings, exit_code = lint_agents(cfg, ["triage"], fail_severity="error")
    codes = [f.code for f in findings]
    assert "UNKNOWN_PURE" not in codes, f"pure not resolved by ca lint: {findings}"
    assert "RESOLVE" not in codes, f"resolve failed: {findings}"
    assert exit_code == 0
```

- [ ] **Step 2: Run it to confirm it fails on current code**

Run: `python -m pytest tests/cli/test_pure_cli_regression.py::test_lint_resolves_pures_no_unknown_pure -v`
Expected: FAIL — findings include `UNKNOWN_PURE — arr function not registered: 'passthrough'`.

- [ ] **Step 3: Add the `lint` action to the child** (`composable_agents/ca/_resolve_child.py`). Insert a handler in `main()` before the default `resolve` tail (after the existing `if action in ("freeze", "freeze_check")` block):

```python
    if action == "lint":
        from composable_agents.validate import validate

        result = _discover_agent(root, src, target)
        if result.found is None:
            _emit({"error": _not_found_error(target, result.import_errors)})
            return 0
        diagnostics = validate(result.found.to_ir())
        _emit(
            {
                "diagnostics": [
                    {"code": d.code, "severity": d.severity, "message": d.message}
                    for d in diagnostics
                ]
            }
        )
        return 0
```

- [ ] **Step 4: Add `_invoke_child`, `LintResolution`, and `lint_agent` to the parent** (`composable_agents/ca/resolve.py`). Refactor `resolve_agent` to use `_invoke_child` so there is one subprocess path:

```python
def _invoke_child(cfg: JulepConfig, extra: dict[str, Any], *, timeout: float = 30.0) -> dict[str, Any]:
    """Run the resolve child with ``{root, src, **extra}`` and return its payload dict.

    On any transport-level failure returns ``{"error": "<message>"}`` so callers
    have a single shape to branch on.
    """
    arg = json.dumps({"root": str(cfg.root), "src": cfg.src, **extra})
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "composable_agents.ca._resolve_child", arg],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(cfg.root),
        )
    except subprocess.TimeoutExpired:
        return {"error": f"resolution timed out after {timeout}s"}
    if proc.returncode != 0:
        return {"error": proc.stderr.strip() or "resolver failed"}
    try:
        return _extract_payload(proc.stdout)
    except (ValueError, json.JSONDecodeError) as exc:
        detail = proc.stderr.strip()
        return {"error": f"{exc}{f': {detail}' if detail else ''}"}


@dataclass(frozen=True)
class LintResolution:
    diagnostics: list[dict[str, str]]
    error: str | None = None


def lint_agent(cfg: JulepConfig, name: str, *, timeout: float = 30.0) -> LintResolution:
    """Validate an agent IN the child (where pures are registered) and return diagnostics."""
    data = _invoke_child(cfg, {"name": name, "action": "lint"}, timeout=timeout)
    if "error" in data:
        return LintResolution(diagnostics=[], error=str(data["error"]))
    raw = data.get("diagnostics", [])
    return LintResolution(diagnostics=[dict(d) for d in raw], error=None)
```

Then simplify `resolve_agent` to reuse `_invoke_child` (behavior identical):

```python
def resolve_agent(cfg: JulepConfig, name: str, *, timeout: float = 30.0) -> ResolvedAgent:
    """Import the user's module in a subprocess and return the agent's serialized IR."""
    data = _invoke_child(cfg, {"name": name}, timeout=timeout)
    if "error" in data:
        return ResolvedAgent(name=name, ir={}, error=str(data["error"]))
    return ResolvedAgent(name=str(data["name"]), ir=data["ir"], error=None)
```

(Default `action` in the child remains `"resolve"`, so omitting it preserves IR-only behavior.)

- [ ] **Step 5: Rewire `lint_agents`** (`composable_agents/ca/lint.py`) to use `lint_agent` instead of `resolve_agent` + in-parent `validate`:

```python
from __future__ import annotations

from dataclasses import dataclass

from composable_agents.ca.config import JulepConfig
from composable_agents.ca.resolve import lint_agent

_SEVERITY_ORDER = {"info": 0, "warning": 1, "error": 2}


@dataclass(frozen=True)
class Finding:
    agent: str
    code: str
    severity: str
    message: str


def lint_agents(
    cfg: JulepConfig,
    names: list[str],
    *,
    fail_severity: str,
) -> tuple[list[Finding], int]:
    """Validate agents (in-child, where pures are live) and gate by severity."""
    if fail_severity not in _SEVERITY_ORDER:
        raise ValueError(
            f"unknown fail_severity {fail_severity!r}; expected one of {sorted(_SEVERITY_ORDER)}"
        )
    floor = _SEVERITY_ORDER[fail_severity]
    findings: list[Finding] = []
    gated = False

    for name in names:
        resolution = lint_agent(cfg, name)
        if resolution.error is not None:
            return [Finding(name, "RESOLVE", "error", resolution.error)], 2
        for d in resolution.diagnostics:
            severity = d["severity"]
            findings.append(Finding(name, d["code"], severity, d["message"]))
            if _SEVERITY_ORDER.get(severity, _SEVERITY_ORDER["error"]) >= floor:
                gated = True

    return findings, 1 if gated else 0
```

- [ ] **Step 6: Run the lint regression + existing lint tests**

Run: `python -m pytest tests/cli/test_pure_cli_regression.py::test_lint_resolves_pures_no_unknown_pure tests/cli/test_lint.py -v`
Expected: PASS (3 tests).

- [ ] **Step 7: Run the gates**

Run: `ruff check composable_agents && uv run mypy --strict composable_agents`
Expected: clean.

- [ ] **Step 8: Commit**

```bash
git add composable_agents/ca/_resolve_child.py composable_agents/ca/resolve.py composable_agents/ca/lint.py tests/cli/test_pure_cli_regression.py
git commit -m "fix(ca): validate in the resolve child so ca lint resolves @pure helpers"
```

---

### Task 3: Child-side `run` action + parent `run_agent`; rewire `run_agent_local`

**Files:**
- Modify: `composable_agents/ca/_resolve_child.py`
- Modify: `composable_agents/ca/resolve.py`
- Modify: `composable_agents/ca/runner.py`
- Test: `tests/cli/test_pure_cli_regression.py` (extend)

**Interfaces:**
- Consumes: `_echo.build_echo_env` (Task 1); `composable_agents.execution.interpreter.interpret`; `ProjectionEvent.to_json/from_json` (existing in `composable_agents.projection`).
- Produces (consumed by `runner.py`):
  - `composable_agents.ca.resolve.RunResolution(value: Any, events: list[dict[str, Any]], error: str | None)`
  - `composable_agents.ca.resolve.run_agent(cfg: JulepConfig, name: str, value: Any, *, timeout: float = 30.0) -> RunResolution`

- [ ] **Step 1: Write the failing regression test (run half)**

Append to `tests/cli/test_pure_cli_regression.py`:

```python
def test_run_executes_pures_no_unknown_pure(pure_module: Path) -> None:
    from composable_agents.ca.config import load_config
    from composable_agents.ca.resolve import resolve_agent  # noqa: F401 (kept available)
    from composable_agents.ca.runner import run_agent_local
    from composable_agents.ca.resolve import resolve_agent as _ra

    cfg = load_config(pure_module)
    # run_agent_local takes a ResolvedAgent today; after Task 3 it ignores the IR
    # and re-runs in the child, but we still pass one for signature stability.
    resolved = _ra(cfg, "triage")
    outcome = run_agent_local(resolved, "TICKET-42", run_id="t-pure")
    assert outcome.error is None, f"run failed: {outcome.error}"
    # The pure actually executed: its output ('seen') survives into the value.
    assert isinstance(outcome.value, dict) and "seen" in outcome.value
```

> Note: today `run_agent_local` interprets in-parent, so this fails with an
> "unknown pure 'passthrough'" error. After Task 3 it runs in the child.

- [ ] **Step 2: Run it to confirm it fails on current code**

Run: `python -m pytest tests/cli/test_pure_cli_regression.py::test_run_executes_pures_no_unknown_pure -v`
Expected: FAIL — `outcome.error` contains `unknown pure 'passthrough'`.

- [ ] **Step 3: Add the `run` action to the child** (`composable_agents/ca/_resolve_child.py`), after the `lint` block:

```python
    if action == "run":
        import asyncio

        from composable_agents.ca._echo import build_echo_env
        from composable_agents.execution.interpreter import interpret

        result = _discover_agent(root, src, target)
        if result.found is None:
            _emit({"error": _not_found_error(target, result.import_errors), "events": []})
            return 0
        node = result.found.to_ir()
        env, projection = build_echo_env(node)
        try:
            outcome = asyncio.run(interpret(node, payload.get("value"), env))
        except Exception as exc:  # noqa: BLE001 - serialize run failure for the parent.
            _emit(
                {
                    "value": None,
                    "events": [e.to_json() for e in projection.events()],
                    "error": str(exc),
                }
            )
            return 0
        _emit(
            {
                "value": outcome.value,
                "events": [e.to_json() for e in projection.events()],
                "error": None,
            }
        )
        return 0
```

- [ ] **Step 4: Add `RunResolution` + `run_agent` to the parent** (`composable_agents/ca/resolve.py`):

```python
@dataclass(frozen=True)
class RunResolution:
    value: Any
    events: list[dict[str, Any]]
    error: str | None = None


def run_agent(cfg: JulepConfig, name: str, value: Any, *, timeout: float = 30.0) -> RunResolution:
    """Interpret an agent IN the child (echo env, pures live) and return value + events."""
    data = _invoke_child(cfg, {"name": name, "action": "run", "value": value}, timeout=timeout)
    if "error" in data and "value" not in data:
        # transport-level failure (timeout / nonzero / parse) -> no events available
        return RunResolution(value=None, events=[], error=str(data["error"]))
    return RunResolution(
        value=data.get("value"),
        events=[dict(e) for e in data.get("events", [])],
        error=data.get("error"),
    )
```

- [ ] **Step 5: Rewire `run_agent_local`** (`composable_agents/ca/runner.py`) to delegate to the child and rebuild `ProjectionEvent`s:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from composable_agents.ca.resolve import ResolvedAgent, run_agent
from composable_agents.projection import ProjectionEvent


@dataclass(frozen=True)
class RunOutcome:
    run_id: str
    value: Any
    events: list[ProjectionEvent] = field(default_factory=list)
    error: str | None = None


def run_agent_local(resolved: ResolvedAgent, value: Any, *, run_id: str) -> RunOutcome:
    """Execute an agent locally by interpreting it in the resolve child.

    The child imports the user module (so @pure helpers are registered) and runs
    the same in-memory echo interpreter the parent used to run, returning the value
    plus serialized projection events for the trace tree.
    """
    if resolved.error is not None:
        return RunOutcome(run_id=run_id, value=None, events=[], error=resolved.error)

    # ``resolved`` is produced by the same config; re-resolve+run in one child call.
    from composable_agents.ca.config import JulepConfig  # local import: avoid cycle at module load

    # The caller already resolved; we need the cfg to invoke the child. cli.run passes
    # a freshly resolved agent, so re-derive cfg-less by re-running through run_agent is
    # not possible without cfg. See Step 6 for the cli wiring change that threads cfg.
    raise NotImplementedError  # replaced in Step 6
```

> The current `run_agent_local(resolved, value, run_id)` signature has no `cfg`,
> but the child needs `cfg.root`/`cfg.src`. Step 6 changes the call site and the
> signature to thread `cfg` + `name`.

- [ ] **Step 6: Change the signature to thread `cfg` + `name`, and update the call site.** Replace the Step-5 body with the real implementation:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from composable_agents.ca.config import JulepConfig
from composable_agents.ca.resolve import RunResolution, run_agent
from composable_agents.projection import ProjectionEvent


@dataclass(frozen=True)
class RunOutcome:
    run_id: str
    value: Any
    events: list[ProjectionEvent] = field(default_factory=list)
    error: str | None = None


def run_agent_local(cfg: JulepConfig, name: str, value: Any, *, run_id: str) -> RunOutcome:
    """Execute an agent locally by interpreting it in the resolve child (pures live)."""
    resolution: RunResolution = run_agent(cfg, name, value)
    events = [ProjectionEvent.from_json(e) for e in resolution.events]
    return RunOutcome(run_id=run_id, value=resolution.value, events=events, error=resolution.error)
```

Update the test from Step 1 to the new signature:

```python
    cfg = load_config(pure_module)
    outcome = run_agent_local(cfg, "triage", "TICKET-42", run_id="t-pure")
```

Update the local-run branch of `cli.run` (`composable_agents/ca/cli.py`, around lines 151-160) to the new signature (it currently does `resolved = resolve_agent(cfg, name); outcome = run_agent_local(resolved, parsed, run_id=rid)`):

```python
    rid = run_id or f"julep-{name}-local"
    outcome = run_agent_local(cfg, name, parsed, run_id=rid)
    if outcome.error is not None:
        typer.echo(f"error: {outcome.error}", err=True)
        save_run(str(cfg.root), run_id=rid, agent=name, status="error", events=outcome.events)
        raise typer.Exit(1)
    typer.echo(render_tree(outcome.events))
    typer.echo(f"\noutput: {_json.dumps(outcome.value)}")
    save_run(str(cfg.root), run_id=rid, agent=name, status="done", events=outcome.events)
```

Remove the now-unused `resolve_agent` import in `cli.py` only if no other command uses it (it is used elsewhere — keep it).

- [ ] **Step 7: Run the run regression + existing run tests**

Run: `python -m pytest tests/cli/test_pure_cli_regression.py tests/cli/test_run.py -v`
Expected: PASS. If `tests/cli/test_run.py` constructs `run_agent_local(resolved, ...)` directly, update those call sites to `run_agent_local(cfg, name, ...)` (the test already has a `cfg`/`sample_module`); show the diff in the commit.

- [ ] **Step 8: Run the gates**

Run: `python -m pytest tests/cli -q && ruff check composable_agents && uv run mypy --strict composable_agents`
Expected: clean.

- [ ] **Step 9: Commit**

```bash
git add composable_agents/ca/_resolve_child.py composable_agents/ca/resolve.py composable_agents/ca/runner.py composable_agents/ca/cli.py tests/cli/test_pure_cli_regression.py tests/cli/test_run.py
git commit -m "fix(ca): interpret in the resolve child so ca run executes @pure helpers"
```

---

### Task 4: End-to-end CLI regression through the real entry point + docs note

Function-level tests (Tasks 2–3) prove the resolve boundary is fixed; this proves the user-facing `ca` command works and locks it forever.

**Files:**
- Modify: `tests/cli/test_pure_cli_regression.py` (add an e2e test)
- Modify: `docs-site/content/docs/guides/using-the-cli.md` (one clarifying note)

**Interfaces:**
- Consumes: the installed CLI module `python -m composable_agents.ca.cli` (entry point `ca = composable_agents.ca.cli:main`).

- [ ] **Step 1: Write the e2e CLI test**

Append to `tests/cli/test_pure_cli_regression.py`:

```python
import subprocess
import sys


def test_cli_lint_and_run_end_to_end(pure_module: Path) -> None:
    base = [sys.executable, "-m", "composable_agents.ca.cli"]
    lint = subprocess.run(
        base + ["lint", "triage"], cwd=pure_module, capture_output=True, text=True
    )
    assert lint.returncode == 0, lint.stdout + lint.stderr
    assert "UNKNOWN_PURE" not in (lint.stdout + lint.stderr)

    run = subprocess.run(
        base + ["run", "triage", "--input", '"TICKET-42"'],
        cwd=pure_module,
        capture_output=True,
        text=True,
    )
    assert run.returncode == 0, run.stdout + run.stderr
    assert "unknown pure" not in (run.stdout + run.stderr).lower()
    assert "output:" in run.stdout
```

- [ ] **Step 2: Run it**

Run: `python -m pytest tests/cli/test_pure_cli_regression.py::test_cli_lint_and_run_end_to_end -v`
Expected: PASS.

- [ ] **Step 3: Add a docs note distinguishing `ca run` (echo) from `dry_run` (realistic).** In `docs-site/content/docs/guides/using-the-cli.md`, under the "Inner loop — local" section, after the trace-tree example, add:

```markdown
> `ca run` executes with **offline echo stubs** for tools and reasoners (each
> returns `{"output": <input>}`) so it never needs a key or network — it is for
> seeing the **trace tree and control flow**, not realistic values. For realistic
> local output, use `deployment.dry_run(input, reasoners={...})` with fake
> reasoners (see [Your First Flow](/docs/start/first-flow)). Registered `@pure`
> functions run for real in both.
```

- [ ] **Step 4: Full gate**

Run: `python -m pytest tests/cli -q && ruff check composable_agents && uv run mypy --strict composable_agents`
Expected: clean.

- [ ] **Step 5: Commit**

```bash
git add tests/cli/test_pure_cli_regression.py docs-site/content/docs/guides/using-the-cli.md
git commit -m "test(ca): e2e regression for ca lint/run over @pure flows + docs note"
```

---

## Notes / known limitations (out of scope for WS1)

- **`ca run` echo semantics are lossy.** Because tools/reasoners echo `{"output":
  <input>}`, a pure that indexes a specific tool-output key (e.g. `hit["queue"]`)
  will `KeyError` *after* this fix — that is pre-existing echo behavior, not the
  pure-registry bug. The Task 4 docs note records this; making `ca run` accept
  fake handlers like `dry_run` is a separate enhancement, not WS1.
- **Input size.** The run value crosses parent→child as JSON in `argv`, matching
  the existing `root/src/name` payload channel. Fine for typical inputs; very
  large inputs would hit OS arg-length limits. Out of scope.

## Self-review

- **Spec coverage (§4 of the design):** root cause (§4.2) → Tasks 2–3 move
  validate/interpret in-child; Approach B (§4.3) → the `_echo` extraction + child
  `lint`/`run` actions + thin parent; regression test (§4.4) → Tasks 2–4 (function
  + e2e); acceptance (§4.5: quickstart **and** multi-pure/`each` flow succeed) →
  the regression uses a `@pure` flow; **add** to executor: also run the original
  experiment `returns_triage.py` (multi-pure + `each`) once via `ca lint` as a
  manual acceptance check before closing WS1.
- **Placeholder scan:** Step 5 of Task 3 intentionally shows a `NotImplementedError`
  stub that Step 6 replaces — this is a deliberate two-step (discover the missing
  `cfg`, then fix the signature), not a placeholder; every other step has complete
  code.
- **Type consistency:** `run_agent_local(cfg, name, value, *, run_id)` is the final
  signature used in both the test (Task 3 Step 6) and `cli.run` (Task 3 Step 6);
  `RunResolution`/`LintResolution` field names (`value`/`events`/`error`,
  `diagnostics`/`error`) match between `resolve.py` definitions and their consumers
  in `runner.py`/`lint.py`. `_invoke_child` returns `dict[str, Any]` consumed
  uniformly by `resolve_agent`/`lint_agent`/`run_agent`.
