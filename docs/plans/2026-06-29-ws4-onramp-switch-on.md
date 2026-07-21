# WS4 — On-Ramp Ladder + `switch_on` Branching Sugar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Lower the two steepest on-ramp frictions the DX experiment surfaced: (1) add `switch_on(subject, key=…, cases=…, default=…)` — branching sugar for the dominant "route on a record field" case, so users don't hand-write+register a selector pure (the experiment's codex avoided `cond`/`switch` entirely); (2) add a progressive, runnable "ladder" tutorial that introduces one surface at a time.

**Architecture:** `switch_on` is sugar over the existing `switch` (`define.py:631`). It derives a deterministic selector — `str(subject[key])` — and registers it as a **source-pinned** pure via `register_pure_with_source(name, fn, source)` (`purity.py:91`), which hashes the *provided source string* (not `inspect.getsource`), so a closure runtime-fn is fine and the determinism contract holds. It then delegates to `switch`. No IR/wire change: `switch_on` lowers to exactly the `switch`/`alt` a hand-written selector would produce. The ladder is a set of runnable doc pages executed by the WS2 doc-runner.

**Tech Stack:** Python 3.12+, `composable_agents/define.py`, `composable_agents/purity.py`/`registry.py`, pytest, docs under `docs-site/content/docs/`.

## Global Constraints

- Python **3.12+**.
- **Determinism contract preserved:** the derived selector is registered *by source* with a name that is a pure function of `key` (same `key` → same name → same source hash → idempotent). No lambdas/closures hashed via `inspect.getsource` (we pass explicit source to `register_pure_with_source`).
- **No wire change:** `switch_on(...)` must produce the same IR as the equivalent hand-written `switch(selector, subject, cases=...)`; the golden corpus must not move for existing flows.
- **Sequencing:** lands after WS2 (so the ladder pages are executed by the doc-runner) and after WS5 (so examples use object-first reasoners).
- Gates clean before each commit: `python -m pytest -q`, `uv run mypy --strict composable_agents`, `ruff check composable_agents`.

## File Structure

- **Modify** `composable_agents/define.py` — add `switch_on(...)` next to `switch` (~line 631); export it.
- **Modify** `composable_agents/__init__.py` — add `switch_on` to imports + `__all__`.
- **Test:** `tests/test_switch_on.py` (new).
- **Create** `docs-site/content/docs/start/ladder.md` — the progressive tutorial (runnable steps).
- **Modify** `docs-site/content/docs/start/meta.json` — add `ladder` to the nav.
- **Modify** `docs-site/content/docs/guides/authoring-flows.md` — a clear `switch`/`switch_on`-with-captures example near the branching section (~line 189-227).

---

### Task 1: Implement `switch_on` (derived, source-pinned selector)

**Files:**
- Modify: `composable_agents/define.py` (add `switch_on` near `switch` at ~line 631)
- Modify: `composable_agents/__init__.py` (export)
- Test: `tests/test_switch_on.py`

**Interfaces:**
- Consumes: `switch(...)` (`define.py:631`), `register_pure_with_source(name, fn, source)` (`purity.py:91`), `is_registered(name)` (`purity.py:104`).
- Produces: `switch_on(subject: Handle, *, key: str, cases: dict[str, FlowDef | BoundFlow], default: FlowDef | BoundFlow | None = None) -> Handle`.

- [ ] **Step 1: Confirm the `register_pure_with_source` contract.** Read `composable_agents/registry.py:166-192` (the `register_pure_with_source` backend) and `purity.py:87-101`. Confirm: it registers `name` with `source_hash = _text_hash(source)` and `fn` as the runtime callable, and does **not** require the source string to contain a `@pure` decorator (that requirement belongs to `register_pure_from_source`). If `register_pure_with_source` *does* require a decorator line, generate the source with one (`@pure("<name>")\ndef _sel(value): ...`). Note which form applies before writing Step 4.

- [ ] **Step 2: Confirm what the `switch` selector receives.** Read `switch` (`define.py:631-689`) and the lowering in `dag.py:884-922`. Confirm a registered selector passed as `switch(selector, subject, …)` receives the **subject value** (the record) and must return the **case-key string**. (If the path instead delivers a plucked sub-field, adjust the selector body in Step 4 accordingly — the Step-6 dry-run test is the empirical check.)

- [ ] **Step 3: Write the failing test** (`tests/test_switch_on.py`):

```python
from composable_agents import deploy, flow, pure, switch_on, tool
from composable_agents.purity import is_registered


@pure("ws4_mark_review")
def mark_review(req: dict) -> dict:
    return {"decision": "review", "action": req["action"]}


@pure("ws4_mark_auto")
def mark_auto(req: dict) -> dict:
    return {"decision": "auto", "action": req["action"]}


@flow
def review(req: dict) -> dict:        # arm param label matches the subject handle label 'req'
    return mark_review(req)


@flow
def auto(req: dict) -> dict:
    return mark_auto(req)


@flow
def route(req: dict) -> dict:
    return switch_on(req, key="action", cases={"review": review, "auto": auto}, default=auto)


def test_switch_on_routes_by_field() -> None:
    dep = deploy(route, tools=[])
    assert dep.dry_run({"action": "review"}).value == {"decision": "review", "action": "review"}
    assert dep.dry_run({"action": "auto"}).value == {"decision": "auto", "action": "auto"}


def test_switch_on_selector_is_registered_and_source_pinned() -> None:
    # Defining `route` (above) must have minted + registered a deterministic selector pure.
    assert is_registered("switch_on.action")
```

- [ ] **Step 4: Run to confirm failure**

Run: `python -m pytest tests/test_switch_on.py -v`
Expected: FAIL — `ImportError: cannot import name 'switch_on'`.

- [ ] **Step 5: Implement `switch_on`** in `define.py` (right after `switch`):

```python
def switch_on(
    subject: Handle,
    *,
    key: str,
    cases: dict[str, "FlowDef | BoundFlow"],
    default: "FlowDef | BoundFlow | None" = None,
) -> Handle:
    """Branch on the value of one field of ``subject`` — declarative sugar over ``switch``.

    Derives a deterministic selector pure ``str(subject[key])`` and registers it by
    source (so it is source-pinned like any ``@pure``), then delegates to ``switch``.
    Same ``key`` → same registered selector (idempotent); the determinism contract holds
    without you hand-writing and registering a predicate. ``cases`` keys are matched by
    string equality against the field value.
    """
    from .purity import is_registered, register_pure_with_source

    selector_name = f"switch_on.{key}"
    if not is_registered(selector_name):
        source = f"def _switch_on_selector(value):\n    return str(value[{key!r}])\n"

        def _selector(value: Any) -> str:
            return str(value[key])

        register_pure_with_source(selector_name, _selector, source)
    return switch(selector_name, subject, cases=cases, default=default)
```

(If Step 1 found a decorator is required, prefix `source` with `@pure({selector_name!r})\n`. If Step 2 found the selector receives a plucked field rather than the whole record, change the body to read that field directly.)

- [ ] **Step 6: Export it.** In `composable_agents/__init__.py`, add `switch_on as switch_on` to the `from .define import (...)` block (next to `switch`) and `"switch_on",` to `__all__` (next to `"switch"`).

- [ ] **Step 7: Run the tests + golden guard**

Run: `python -m pytest tests/test_switch_on.py -v && python -m pytest tests/golden -q`
Expected: PASS, golden unchanged (a hand-written `switch` with an equivalent selector lowers identically; `switch_on` adds no new IR shape).

- [ ] **Step 8: Gates + commit**

```bash
git add composable_agents/define.py composable_agents/__init__.py tests/test_switch_on.py
ruff check composable_agents && uv run mypy --strict composable_agents
git commit -m "feat(define): add switch_on(subject, key=, cases=) branching sugar (source-pinned selector)"
```

---

### Task 2: Progressive "ladder" tutorial + a branching example

**Files:**
- Create: `docs-site/content/docs/start/ladder.md`
- Modify: `docs-site/content/docs/start/meta.json` (nav)
- Modify: `docs-site/content/docs/guides/authoring-flows.md` (branching section ~line 189-227)
- Test: covered by WS2's `tests/test_docs_executable.py` (the doc-runner executes these blocks)

**Interfaces:** consumes `switch_on` (Task 1) and the object-first reasoner idiom (WS5).

- [ ] **Step 1: Write `start/ladder.md`** as a single page that climbs one surface per step, each step a runnable block the WS2 doc-runner will execute. Steps, each building on the last:
  1. **A tool** — `@tool` returning canned data; call it from a one-line `@flow`; `deploy(...).dry_run(...)`.
  2. **A pure** — add a `@pure` that reshapes the tool output; show `hit["key"]` pluck and `a | b` merge.
  3. **A reasoner** — declare a `Reasoner(...)` object (object-first, WS5), call `think(reasoner, prompt)`, run via `dry_run(reasoners={name: fake})`.
  4. **Branching** — route with `switch_on(subject, key="action", cases={...})`; explain it is sugar over `switch` and that `cases` match the field's string value.
  5. **Fan-out** — `each(body, items, max_parallel=…)` over a list; note the body item param is positional.
  6. **Deploy & inspect** — `deployment.surface_shape`, `prod_gap_summary()`, and the keyless `dry_run` story.

  Each fenced block must be a complete runnable program (imports + flow + deploy + dry_run + print), tagged `<!-- julep:doctest expect-output -->` with a following ```text``` block where the output is stable, else left as default-run (no pragma). Mark any partial illustrative snippet `<!-- julep:doctest skip -->`. End-state mirrors the experiment's returns-triage task so the ladder doubles as a worked example.

- [ ] **Step 2: Add `ladder` to the nav.** In `start/meta.json`, insert `"ladder"` into the `pages` array in reading order (after `first-flow`, before `next-steps`). Match the existing JSON shape exactly.

- [ ] **Step 3: Add a branching example to `authoring-flows.md`.** In the "Branching and Fan-Out" section (~line 189-227), after the existing `cond`/`switch` prose, add a short, copy-pasteable example showing BOTH:
  - the explicit form: a registered `@pure` selector + `switch(selector, subject, cases=..., default=...)`, with the arm whose remaining parameter matches the subject label (make the subject-label/keyword-capture rule concrete); and
  - the sugar: the same routing via `switch_on(subject, key="...", cases={...})`, noting it auto-derives the selector.

  Tag the runnable block per the WS2 convention so the doc-runner executes it.

- [ ] **Step 4: Run the doc-runner over the new/changed pages**

Run: `python -m pytest tests/test_docs_executable.py -v -k "ladder or authoring or first"`
Expected: PASS — every tagged block in `ladder.md` and the new `authoring-flows.md` example runs clean (and `expect-output` blocks match). (Requires WS2 Task 1-2 to be merged; if running WS4 first, run the blocks manually with `python -c` per the WS2 executor logic.)

- [ ] **Step 5: Commit**

```bash
git add docs-site/content/docs/start/ladder.md docs-site/content/docs/start/meta.json docs-site/content/docs/guides/authoring-flows.md
git commit -m "docs: add progressive ladder tutorial + switch_on/switch branching example"
```

---

## Self-review

- **Spec coverage (§7 of the design):** `switch_on(subject, key=, cases=, default=)` sugar that auto-derives a source-pinned selector → Task 1; progressive one-surface-at-a-time ladder → Task 2 Step 1; copy-pasteable `cond`/`switch`-with-captures example making the subject-label rule obvious → Task 2 Step 3; determinism preserved (registered, source-pinned selector) → Task 1 Steps 1/5 + the `is_registered` test; no wire change → Task 1 Step 7 golden guard.
- **Placeholder scan:** Task 1 has the full `switch_on` code; Steps 1-2 are explicit verification reads with defined fallbacks ("if X, then Y") rather than open TODOs. Task 2 Step 1 enumerates the six concrete ladder steps and the exact pragma rules from WS2 (not "write a tutorial"). The one genuine dependency is WS2's doc-runner (called out in Step 4).
- **Type consistency:** `switch_on(subject, *, key, cases, default=None) -> Handle` (Task 1 Step 5) is the signature exported (Step 6) and exercised in `tests/test_switch_on.py` (Step 3); the derived pure name `f"switch_on.{key}"` is used identically in the impl and the `is_registered("switch_on.action")` assertion.
