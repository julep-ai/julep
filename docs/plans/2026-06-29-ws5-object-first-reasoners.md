# WS5 — Object-First Reasoners & Idiom Hard Cut-Over Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make reasoners declarative and object-first — declare a `Reasoner(...)`, reference it directly in `think(obj, …)`, and collect it at `deploy(reasoners=[obj])`/`Agent(reasoner=obj)` — and remove the imperative `register_reasoner` and the duplicate `reply_schema=` constructor param outright (no compat).

**Architecture:** The authoring verb `think(reasoner_or_name, …)` already accepts a `Reasoner` object (`define.py:571`, normalized via `_reasoner_name`). The gaps are: (1) `deploy(reasoners=…)` only *validates* names (`deploy.py:503` → `_capabilities_from_tools`), it does not register objects; (2) `Agent(reasoner=)` takes a string only; (3) the public imperative `register_reasoner` exists; (4) `Reasoner(...)` exposes both `reply=` and `reply_schema=`. We make `deploy`/`Agent` register passed `Reasoner` objects (mirroring how `tools=[obj]` already works), drop the public `register_reasoner` and the `reply_schema=` param, and migrate every example/doc/test. The frozen wire format is unchanged (`ThinkStep.reasoner` is still a name; the capability `reasoners` section is still a name list), so the golden corpus must not move.

**Tech Stack:** Python 3.12+, `composable_agents` package (`dotctx.py`, `registry.py`, `deploy.py`, `agent.py`, `define.py`, `__init__.py`), pytest, the golden corpus under `tests/golden/`.

## Global Constraints

- Python **3.12+**.
- **Hard cut-over, no backward compat / no deprecation shims** (early project — see `early-project-hard-cutover` memory). Remove the old API and fix all callers in the same change.
- **The golden corpus MUST NOT move.** Object-first is an authoring-surface change only; `think(obj,…)` lowers to the identical `ThinkStep(reasoner=obj.name)` and `deploy(reasoners=[obj])` freezes the identical name→config manifest entry. If a golden hash changes, stop — something lowered differently.
- Pure core must not import `temporalio`; only `composable_agents/execution/` may.
- Gates clean before each task's closing commit: `python -m pytest -q`, `uv run mypy --strict composable_agents`, `ruff check composable_agents`.
- **Keep** the registry-query / dynamic-resolution family (`get_reasoner`, `reasoner_from_ctx`, `reasoner_from_settings`, `reasoner_to_flow`, `make_local_reasoner`, `list_reasoners`, `registered_reasoners`) and the **string path** (`think("name",…)`, `reasoners=["name"]`) — these serve dynamic/late-bound selection and stay.

## File Structure

- **Modify** `composable_agents/dotctx.py` — `Reasoner.__init__`: make `reply=` accept a Python type *or* a raw JSON-schema dict; remove the `reply_schema=` parameter (the **stored field** `reply_schema` stays). Demote the module-level `register_reasoner` to internal `_register_reasoner` (used by `reasoner_from_settings`/`load_dotctx`).
- **Modify** `composable_agents/deploy.py` — `reasoners=` accepts `Sequence[str | Reasoner]`; register passed `Reasoner` objects, then normalize to names for the capability manifest.
- **Modify** `composable_agents/agent.py` — `Agent(reasoner=)` accepts `str | Reasoner`; register an object and use its `.name`.
- **Modify** `composable_agents/__init__.py` — remove `register_reasoner` from the import block and `__all__`.
- **Modify** `examples/*.py` (7 files) and `docs-site/content/docs/**` — migrate to object-first.
- **Modify** `tests/**` — migrate ~70 `register_reasoner` call sites; update the `reply`/`reply_schema` tests.
- **Test:** `tests/test_object_first_reasoners.py` (new) — object-first behavior + wire-equality proof.

---

### Task 1: `reply=` accepts type-or-dict; remove `reply_schema=` constructor param

**Files:**
- Modify: `composable_agents/dotctx.py:136-188` (`Reasoner.__init__`)
- Test: `tests/test_dotctx_reply.py` (existing — update), `tests/test_object_first_reasoners.py` (new)

**Interfaces:**
- Produces: `Reasoner(name, model, system="", *, reply=<type|dict|unset>, tools=(), …)` — no `reply_schema=` parameter; the instance still has a `.reply_schema` field (materialized from `reply`).

- [ ] **Step 1: Read the current converter.** Open `composable_agents/dotctx.py:136-188`. Confirm how `reply=` (keyword-only, sentinel `_REPLY_UNSET`) is converted to `reply_schema` (≈ lines 169-179) and what helper does the type→schema conversion. The new code reuses that helper for the `type` case and stores a `dict` as-is.

- [ ] **Step 2: Write the failing test** (`tests/test_object_first_reasoners.py`):

```python
from typing import TypedDict

import pytest

from composable_agents import Reasoner


class Reply(TypedDict):
    answer: str


def test_reply_accepts_typeddict() -> None:
    r = Reasoner(name="r1", model="anthropic:claude-haiku-4-5-20251001", reply=Reply)
    assert isinstance(r.reply_schema, dict) and r.reply_schema  # materialized schema


def test_reply_accepts_raw_schema_dict() -> None:
    schema = {"regime": "str", "confidence": "number"}
    r = Reasoner(name="r2", model="anthropic:claude-haiku-4-5-20251001", reply=schema)
    assert r.reply_schema == schema  # raw dict stored as-is


def test_reply_schema_kwarg_is_gone() -> None:
    with pytest.raises(TypeError):
        Reasoner(  # type: ignore[call-arg]
            name="r3", model="anthropic:claude-haiku-4-5-20251001",
            reply_schema={"answer": "str"},
        )
```

- [ ] **Step 3: Run it to confirm failure**

Run: `python -m pytest tests/test_object_first_reasoners.py -v`
Expected: FAIL — `test_reply_accepts_raw_schema_dict` (dict not accepted by `reply=` today) and `test_reply_schema_kwarg_is_gone` (the kwarg still exists).

- [ ] **Step 4: Edit `Reasoner.__init__`** in `dotctx.py`: remove the `reply_schema: Optional[dict[str, Any]] = None` parameter; keep the keyword-only `reply` param; in the body, materialize:

```python
if reply is not _REPLY_UNSET:
    if isinstance(reply, dict):
        materialized = reply                      # raw JSON-schema dict, stored as-is
    else:
        materialized = _schema_from_type(reply)   # the existing type->schema helper
else:
    materialized = None
object.__setattr__(self, "reply_schema", materialized)
```

(Use the exact name of the existing type→schema converter found in Step 1 in place of `_schema_from_type`. Keep the `reply_schema` *field* on the dataclass.)

- [ ] **Step 5: Update `tests/test_dotctx_reply.py`** — the mutual-exclusivity test at lines ~84-92 no longer applies (there is no `reply_schema=` to conflict with `reply=`). Replace it with assertions that `reply=<TypedDict>` and `reply=<dict>` both populate `.reply_schema`, mirroring Step 2. Update the registration test at lines ~54/76 to construct via `reply=`.

- [ ] **Step 6: Run tests + gates**

Run: `python -m pytest tests/test_object_first_reasoners.py tests/test_dotctx_reply.py -v && ruff check composable_agents && uv run mypy --strict composable_agents`
Expected: PASS / clean.

- [ ] **Step 7: Commit**

```bash
git add composable_agents/dotctx.py tests/test_object_first_reasoners.py tests/test_dotctx_reply.py
git commit -m "feat(reasoner): reply= accepts type or raw schema; drop reply_schema= param"
```

---

### Task 2: `deploy(reasoners=[obj])` registers passed `Reasoner` objects

**Files:**
- Modify: `composable_agents/deploy.py` (`deploy` signature ~line 455; `reasoners=` handling ~line 503; `_capabilities_from_tools` ~line 207)
- Modify: `composable_agents/dotctx.py` (add/confirm an internal registration entry point)
- Test: `tests/test_object_first_reasoners.py`

**Interfaces:**
- Consumes: `Reasoner` (Task 1); `DEFAULT_REGISTRY.register_reasoner` (`registry.py:124`).
- Produces: `deploy(flow, *, tools=[...], reasoners: Sequence[str | Reasoner] = None, …)` — passing a `Reasoner` registers it and uses its name; passing a string keeps today's behavior.

- [ ] **Step 1: Write the failing test** — object-first deploy with NO prior registration, and prove the wire format is identical to the string form:

```python
def _triage_flow():
    from composable_agents import deploy, flow, pure, think, tool

    @tool(effect="read", idempotent=True)
    def lookup(t: str) -> dict:
        return {"q": "billing"}

    @pure("ws5_prompt")
    def prompt(hit: dict) -> dict:
        return {"q": hit["q"]}

    @flow
    def triage(t: str) -> dict:
        hit = lookup(t)
        return think("ws5_reply", prompt(hit)) if False else prompt(hit) | think("ws5_reply", prompt(hit))

    return triage, lookup


def test_deploy_registers_reasoner_object_and_wire_is_identical() -> None:
    from composable_agents import Reasoner, deploy, flow, pure, think, tool

    @tool(effect="read", idempotent=True)
    def lookup(t: str) -> dict:
        return {"q": "billing"}

    @pure("ws5_prompt2")
    def prompt(hit: dict) -> dict:
        return {"q": hit["q"]}

    r = Reasoner(name="ws5_reply2", model="anthropic:claude-haiku-4-5-20251001",
                 system="x", reply={"reply": "str"})

    @flow
    def triage(t: str) -> dict:
        hit = lookup(t)
        return prompt(hit) | think(r, prompt(hit))

    # Object-first: no register_reasoner call anywhere.
    dep = deploy(triage, tools=[lookup], reasoners=[r])
    assert dep.artifact_hash  # froze successfully
    assert "ws5_reply2" in dep.manifest_json  # name landed in the manifest
```

(Trim the throwaway `_triage_flow` helper; keep one clean flow. The key assertion is that deploy succeeds with an unregistered-until-now `Reasoner` object and the name reaches the manifest.)

- [ ] **Step 2: Run it to confirm failure**

Run: `python -m pytest tests/test_object_first_reasoners.py::test_deploy_registers_reasoner_object_and_wire_is_identical -v`
Expected: FAIL — `deploy` rejects/can't handle a `Reasoner` in `reasoners=` (it expects `Sequence[str]`), or the reasoner isn't registered so freeze/validate fails.

- [ ] **Step 3: Widen the `deploy` signature and register objects.** In `deploy.py`:
  - Change the annotation `reasoners: Optional[Sequence[str]]` → `reasoners: Optional[Sequence[str | "Reasoner"]]` (import `Reasoner` under `TYPE_CHECKING` or directly).
  - Immediately before the `_capabilities_from_tools(tools, reasoners)` call (~line 503), normalize:

```python
from .dotctx import Reasoner
from .registry import DEFAULT_REGISTRY

reasoner_names: Optional[list[str]] = None
if reasoners is not None:
    reasoner_names = []
    for r in reasoners:
        if isinstance(r, Reasoner):
            DEFAULT_REGISTRY.register_reasoner(r)   # object-first: declaration via deploy
            reasoner_names.append(r.name)
        else:
            reasoner_names.append(r)
```

  - Pass `reasoner_names` (not `reasoners`) to `_capabilities_from_tools(...)`. The manifest content is byte-identical to passing the same names as strings.

- [ ] **Step 4: Run the test + a golden guard**

Run: `python -m pytest tests/test_object_first_reasoners.py -v && python -m pytest tests/golden -q`
Expected: PASS, and **golden unchanged** (no snapshot diff). If golden moved, stop and investigate — the manifest must be identical to the string path.

- [ ] **Step 5: Gates + commit**

```bash
git add composable_agents/deploy.py tests/test_object_first_reasoners.py
ruff check composable_agents && uv run mypy --strict composable_agents && git commit -m "feat(deploy): reasoners= accepts and registers Reasoner objects"
```

---

### Task 3: `Agent(reasoner=obj)` accepts a `Reasoner` object

**Files:**
- Modify: `composable_agents/agent.py:407-422` (`Agent.__init__`), and the `Agent.replace(...)` path if it also takes `reasoner=`.
- Test: `tests/test_object_first_reasoners.py`

**Interfaces:**
- Produces: `Agent(reasoner: str | Reasoner, tools=(), …)`.

- [ ] **Step 1: Write the failing test**

```python
def test_agent_accepts_reasoner_object() -> None:
    from composable_agents import Agent, Reasoner

    r = Reasoner(name="ws5_ctrl", model="anthropic:claude-haiku-4-5-20251001", reply={"out": "str"})
    agent = Agent(reasoner=r)                 # object, not a string, no prior registration
    # the agent resolved the reasoner by name under the hood
    assert agent is not None
```

- [ ] **Step 2: Run it to confirm failure**

Run: `python -m pytest tests/test_object_first_reasoners.py::test_agent_accepts_reasoner_object -v`
Expected: FAIL (type error / name derivation treats the object as a string).

- [ ] **Step 3: Handle the object in `Agent.__init__`.** At the top of `__init__`, normalize:

```python
from .dotctx import Reasoner
from .registry import DEFAULT_REGISTRY

if isinstance(reasoner, Reasoner):
    DEFAULT_REGISTRY.register_reasoner(reasoner)
    reasoner = reasoner.name
```

Place this before the existing `self._reasoner_model = reasoner` (line ~462) so all downstream code sees the name string, unchanged. Update the parameter annotation to `reasoner: str | Reasoner`. Apply the same normalization in `Agent.replace(...)` if it accepts `reasoner=`.

- [ ] **Step 4: Run + gates + commit**

Run: `python -m pytest tests/test_object_first_reasoners.py -v && ruff check composable_agents && uv run mypy --strict composable_agents`

```bash
git add composable_agents/agent.py tests/test_object_first_reasoners.py
git commit -m "feat(agent): Agent(reasoner=) accepts a Reasoner object"
```

---

### Task 4: Remove public `register_reasoner`; reroute internal callers

**Files:**
- Modify: `composable_agents/__init__.py` (import block ~line 179, `__all__` ~line 312)
- Modify: `composable_agents/dotctx.py` (the module-level `register_reasoner` shim ~line 194; callers at ~266 `reasoner_from_settings`, ~309 `load_dotctx`)
- Modify: `composable_agents/dotctx_rich.py:677` (caller)
- Test: `tests/test_object_first_reasoners.py`, `tests/invariants/test_registry.py`

**Interfaces:**
- Removes from the public API: `composable_agents.register_reasoner`.
- Internal: `DEFAULT_REGISTRY.register_reasoner` (registry method) stays; module-level callers use it directly.

- [ ] **Step 1: Write the failing test** (asserting the public symbol is gone):

```python
def test_register_reasoner_not_public() -> None:
    import composable_agents

    assert not hasattr(composable_agents, "register_reasoner")
    assert "register_reasoner" not in composable_agents.__all__
```

- [ ] **Step 2: Run it to confirm failure**

Run: `python -m pytest tests/test_object_first_reasoners.py::test_register_reasoner_not_public -v`
Expected: FAIL (symbol still exported).

- [ ] **Step 3: Reroute internal callers, then drop the export.**
  - In `dotctx.py`, replace internal uses of the module-level `register_reasoner(...)` (in `reasoner_from_settings` ~line 266 and `load_dotctx` ~line 309) with `DEFAULT_REGISTRY.register_reasoner(...)`. Remove the public module-level `register_reasoner` shim (line ~194-195), or rename it to `_register_reasoner` if any internal site is clearer that way.
  - In `dotctx_rich.py:677`, switch to `DEFAULT_REGISTRY.register_reasoner(...)`.
  - In `composable_agents/__init__.py`: delete `register_reasoner as register_reasoner` from the `from .dotctx import (...)` block (line ~179) and `"register_reasoner",` from `__all__` (line ~312).

- [ ] **Step 4: Confirm `think(obj)` already works (no code change expected).** Add a guard test:

```python
def test_think_accepts_object_at_authoring_time() -> None:
    from composable_agents import Reasoner, flow, pure, think, tool

    @tool(effect="read", idempotent=True)
    def lk(t: str) -> dict:
        return {"q": "b"}

    @pure("ws5_p4")
    def pp(h: dict) -> dict:
        return {"q": h["q"]}

    r = Reasoner(name="ws5_think_obj", model="anthropic:claude-haiku-4-5-20251001", reply={"o": "str"})

    @flow
    def f(t: str) -> dict:
        return pp(lk(t)) | think(r, pp(lk(t)))

    assert f is not None  # @flow define-time accepted think(r, ...)
```

- [ ] **Step 5: Run + gates**

Run: `python -m pytest tests/test_object_first_reasoners.py tests/invariants/test_registry.py -v && ruff check composable_agents && uv run mypy --strict composable_agents`
Expected: PASS (update `tests/invariants/test_registry.py:35/57` which asserted the public shim — point them at `DEFAULT_REGISTRY.register_reasoner`).

- [ ] **Step 6: Commit**

```bash
git add composable_agents/__init__.py composable_agents/dotctx.py composable_agents/dotctx_rich.py tests/test_object_first_reasoners.py tests/invariants/test_registry.py
git commit -m "feat!: remove public register_reasoner (object-first via deploy/Agent/think)"
```

---

### Task 5: Migrate examples and docs to object-first

**Files:**
- Modify: `examples/cluster_labeling_flow.py`, `examples/episode_summary_flow.py`, `examples/session_demo.py`, `examples/reasoner_batch_openai.py`, `examples/reasoner_batch_anthropic.py`, `examples/elnino/swarm.py` (and any other `examples/*.py` that imports `register_reasoner`).
- Modify: `docs-site/content/docs/start/first-flow.md`, `start/first-agent.md`, `reference/flow-api.md`, `reference/cheatsheet.md`, `reference/python-api.md`, and any `guides/*` page showing `register_reasoner`/`reply_schema`.

**Interfaces:** consumes the object-first API from Tasks 1-4.

- [ ] **Step 1: Find every site**

Run: `grep -rn "register_reasoner\|reply_schema" examples docs-site/content`

- [ ] **Step 2: Migrate each by the same transform** (per file): turn

```python
register_reasoner(Reasoner(name="X", model="…", system="…", reply_schema={…}))
...
think("X", h)
...
deploy(flow, tools=[…], reasoners=["X"])
```

into

```python
X = Reasoner(name="X", model="…", system="…", reply={…})   # reply= takes the raw dict
...
think(X, h)
...
deploy(flow, tools=[…], reasoners=[X])
```

Drop the `register_reasoner` import. For examples that build an `Agent`, pass the object: `Agent(reasoner=X, …)`. For docs `.md`, also update prose that says "register the reasoner".

- [ ] **Step 3: Run the examples that have a keyless local path** to confirm they still execute (the ones using `dry_run`/scripted/echo). At minimum:

Run: `python examples/episode_summary_flow.py` (or whichever examples have a no-key local entry point per their `__main__`)
Expected: same output as before the migration.

- [ ] **Step 4: Commit**

```bash
git add examples docs-site/content
git commit -m "docs(examples): migrate to object-first reasoners (think(obj)+deploy(reasoners=[obj]))"
```

---

### Task 6: Migrate the test suite; prove the wire format is unchanged

**Files:**
- Modify: ~15 test files using `register_reasoner` (notably `tests/test_transcripts.py` ~18, `tests/test_e2e_temporal.py` ~10, `tests/test_reasoner_batch.py` ~9, `tests/test_effects_extraction.py`, `tests/test_qos.py`, `tests/test_renderer_deploy.py`, …).
- Add: a leftover-grep gate test.

**Interfaces:** consumes Tasks 1-4.

- [ ] **Step 1: Inventory**

Run: `grep -rln "register_reasoner\|reply_schema" tests | sort`
Record the list; each file is migrated and re-run individually.

- [ ] **Step 2: Migrate per file.** Two cases:
  - **Test deploys/uses the flow:** apply the Task-5 transform (`r = Reasoner(...)`; `think(r, …)`; `deploy(reasoners=[r])` / `Agent(reasoner=r)`).
  - **Test only needs the reasoner in the registry (no deploy)** — e.g. transcript/effect tests that call `think("name")` and run the interpreter directly: replace `register_reasoner(Reasoner(...))` with `DEFAULT_REGISTRY.register_reasoner(Reasoner(...))` (the internal entry point stays). Import `from composable_agents.registry import DEFAULT_REGISTRY`.

  Do NOT blindly sed `register_reasoner → DEFAULT_REGISTRY.register_reasoner`; prefer the object-first form where the test deploys, and the registry form only where it doesn't.

- [ ] **Step 3: Run each migrated file as you go**

Run (per file): `python -m pytest tests/<file> -q`
Expected: PASS.

- [ ] **Step 4: Add the leftover-grep gate** (`tests/test_object_first_reasoners.py`):

```python
import subprocess


def test_no_public_register_reasoner_or_reply_schema_left() -> None:
    # register_reasoner must not appear as a public/import symbol; reply_schema must
    # not appear as a constructor kwarg anywhere in package, examples, or docs.
    out = subprocess.run(
        ["grep", "-rn", "register_reasoner\\|reply_schema=",
         "composable_agents", "examples", "docs-site/content"],
        capture_output=True, text=True,
    ).stdout
    # The only allowed hit is the internal registry method definition.
    leftovers = [
        ln for ln in out.splitlines()
        if "DEFAULT_REGISTRY.register_reasoner" not in ln
        and "def register_reasoner(self" not in ln
    ]
    assert not leftovers, "leftover register_reasoner/reply_schema=: \n" + "\n".join(leftovers)
```

- [ ] **Step 5: Regenerate/verify golden + full gate**

Run: `python -m pytest tests/golden -q`
Expected: **no diff** — the wire format is identical. If a snapshot moved, stop and find the lowering difference (object-first must not change IR/manifest).

Then the full gate:

Run: `python -m pytest -q && ruff check composable_agents && uv run mypy --strict composable_agents`
Expected: all clean.

- [ ] **Step 6: Commit**

```bash
git add tests
git commit -m "test: migrate suite to object-first reasoners; lock out register_reasoner/reply_schema="
```

---

## Self-review

- **Spec coverage (§8 of the design):** object-first `think(obj)`+`deploy(reasoners=[obj])`+`Agent(reasoner=obj)` → Tasks 2-4; remove `register_reasoner` → Task 4; collapse `reply`/`reply_schema` → Task 1; keep the registry-query family + string path → preserved (Tasks 2/4 keep names working; query funcs untouched); migrate all docs/examples/tests → Tasks 5-6; wire-format invariants / golden unchanged → Task 2 Step 4 + Task 6 Step 5; hard cut-over → Task 4 removes the symbol outright.
- **Placeholder scan:** Task 1 Step 4 references `_schema_from_type` as a stand-in for "the existing type→schema converter found in Step 1" — Step 1 explicitly requires identifying its real name first; this is a read-then-use instruction, not a placeholder. The throwaway `_triage_flow` in Task 2 Step 1 is called out to be trimmed. Everything else has concrete code.
- **Type consistency:** `reasoners: Sequence[str | Reasoner]` (Task 2) and `reasoner: str | Reasoner` (Task 3) are the new signatures; both normalize to names before any downstream/wire code, so `ThinkStep.reasoner: str` (`ir.py:270`) and the capability `reasoners` name-list are unchanged. `DEFAULT_REGISTRY.register_reasoner` is the single internal registration entry used by Tasks 2/3/4/6.
