# WS3 — Teaching Define-Time Error Messages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the two define-time errors a newcomer actually hits — passing multiple positional handles to a pure (raw Python `TypeError`), and method-style `flow.each(...)` (a misleading "unregistered callable") — with framework `DefineError`s carrying a `fix:` line, matching the house style already used elsewhere.

**Architecture:** Both fixes are small and local to `composable_agents/`. (1) `apply_if_authoring` (`define.py:795`) already raises a `DefineError` when a step is applied to `>1` positional handle — but it is unreachable for pures because `Pure.__call__(self, value, **kwargs)` only accepts one positional, so Python raises `TypeError` first. We widen `Pure.__call__` to `*args` and route to the existing check (improving its message). (2) `Handle.__getattr__` (`define.py:364`) and a currently-missing `FlowDef.__getattr__` (`define.py:408`) gain a special case for top-level-helper names (`each`, `par`, `seq`, `cond`, `switch`, `map_n`, `reschedule`) that raises a `DefineError` telling the user to call the helper, not a method.

**Tech Stack:** Python 3.12+, `composable_agents/purity.py`, `composable_agents/define.py`, pytest (`tests/test_define_frontend.py`).

## Global Constraints

- Python **3.12+**.
- New messages match the established `DefineError` format: `f"<what>{_source_suffix(span)}; <imperative fix>"` (`_source_suffix` at `define.py:1489-1497`). `DefineError` is defined at `define.py:74-76`.
- Do not change runtime behavior of a correctly-authored flow — only the *error path* for misuse. The golden corpus must not move (these are authoring-time exceptions, not IR).
- Gates clean before each commit: `python -m pytest -q`, `uv run mypy --strict composable_agents`, `ruff check composable_agents`.

## File Structure

- **Modify** `composable_agents/purity.py:42-48` — widen `Pure.__call__` to accept `*args` so the framework arity check is reachable.
- **Modify** `composable_agents/define.py` — improve the arity `DefineError` message (~line 795); add top-level-helper detection to `Handle.__getattr__` (~line 364) and a new `FlowDef.__getattr__` (~line 408); add a shared helper-name set near `_CONTROL_HELPERS` (line 69).
- **Test:** `tests/test_define_frontend.py` (extend).

---

### Task 1: Pure-call arity → a teaching `DefineError`

**Files:**
- Modify: `composable_agents/purity.py:42-48`
- Modify: `composable_agents/define.py` (the arity message at ~line 795)
- Test: `tests/test_define_frontend.py`

**Interfaces:**
- Consumes: `apply_if_authoring(fn, args, kwargs)` (`define.py:780`), `DefineError` (`define.py:74`).
- Produces: calling a registered `@pure` inside `@flow` with `>1` positional handle raises `DefineError` (not `TypeError`).

- [ ] **Step 1: Read the current code.** Open `purity.py:42-48` and `define.py:780-807`. Confirm:
  - `Pure.__call__(self, value, **kwargs)` → `apply_if_authoring(self, (value,), kwargs)` then `return self.fn(value, **kwargs)`.
  - `apply_if_authoring` returns `NotImplemented` when *not* authoring, and the `if len(args) > 1: raise DefineError(...)` at ~795-796 sits inside the authoring branch (verify the ordering: the arity error must only fire when authoring, so the runtime path with one value is unaffected).

- [ ] **Step 2: Write the failing test** (`tests/test_define_frontend.py`):

```python
def test_pure_called_with_two_handles_gives_fix_line() -> None:
    from composable_agents import flow, pure, tool
    from composable_agents.define import DefineError

    @tool(effect="read", idempotent=True)
    def lk(t: str) -> dict:
        return {"a": 1, "b": 2}

    @pure("ws3_two_arg")
    def combine(a: dict, b: dict) -> dict:  # author mistakenly expects two handles
        return {**a, **b}

    with pytest.raises(DefineError, match=r"one input value.*merge.*\|"):
        @flow
        def bad(t: str) -> dict:
            hit = lk(t)
            return combine(hit, hit)   # two positional handles -> should be a DefineError
```

- [ ] **Step 3: Run to confirm failure**

Run: `python -m pytest tests/test_define_frontend.py::test_pure_called_with_two_handles_gives_fix_line -v`
Expected: FAIL — raises `TypeError: Pure.__call__() takes 2 positional arguments but 3 were given`, not `DefineError`.

- [ ] **Step 4: Widen `Pure.__call__`** (`purity.py:42-48`):

```python
def __call__(self, *args: Any, **kwargs: Any) -> Any:
    from .define import apply_if_authoring

    authored = apply_if_authoring(self, args, kwargs)
    if authored is not NotImplemented:
        return authored
    return self.fn(*args, **kwargs)
```

- [ ] **Step 5: Improve the arity message** in `define.py` (~line 795). Change the existing raise to name the rule and the fix:

```python
if len(args) > 1:
    raise DefineError(
        f"a pure/step takes one input value plus JSON keyword constants"
        f"{_source_suffix(_current_source())}; you passed {len(args)} positional handles. "
        "Merge them into one record first with 'a | b' (std.merge), or reshape with a pure, "
        "then call on the single handle."
    )
```

(Use whatever source-span accessor `apply_if_authoring` already has in scope for `_source_suffix`; if none, pass the span it already computes. The exact helper is visible in Step 1.)

- [ ] **Step 6: Run + gates**

Run: `python -m pytest tests/test_define_frontend.py -v && ruff check composable_agents && uv run mypy --strict composable_agents`
Expected: PASS / clean. (Also run the broader pure/runtime tests — `python -m pytest tests/ -k pure -q` — to confirm the `*args` widening didn't change runtime pure execution.)

- [ ] **Step 7: (Quick check) does `Tool.__call__` share the limitation?** Grep `composable_agents/agent.py`/`tool.py` for `Tool.__call__`. If it also has a single-positional signature and routes through `apply_if_authoring`, apply the same `*args` widening so tools get the same teaching error. If its signature already accepts the authoring path, leave it. Note the outcome in the commit message.

- [ ] **Step 8: Commit**

```bash
git add composable_agents/purity.py composable_agents/define.py tests/test_define_frontend.py
git commit -m "fix(define): pure called with >1 handle raises a DefineError with a merge fix, not TypeError"
```

---

### Task 2: Method-style combinators → a teaching `DefineError`

**Files:**
- Modify: `composable_agents/define.py` (helper-name set near line 69; `Handle.__getattr__` ~line 364; new `FlowDef.__getattr__` ~line 408)
- Test: `tests/test_define_frontend.py`

**Interfaces:**
- Consumes: `DefineError`, `_source_suffix`, `_CONTROL_HELPERS` (`define.py:69`).
- Produces: accessing `each`/`par`/`seq`/`cond`/`switch`/`map_n`/`reschedule` as an attribute on a `Handle` or a `FlowDef` raises a `DefineError` naming the top-level-helper fix.

- [ ] **Step 1: Write the failing tests** (`tests/test_define_frontend.py`):

```python
def test_flowdef_dot_each_gives_top_level_hint() -> None:
    from composable_agents import flow, tool
    from composable_agents.define import DefineError

    @tool(effect="read", idempotent=True)
    def lk(t: str) -> dict:
        return {"x": 1}

    @flow
    def body(item: dict) -> dict:
        return lk("x") | item if False else item

    with pytest.raises(DefineError, match=r"each is a top-level helper.*each\(body, items"):
        @flow
        def outer(items: list) -> object:
            return body.each(items)        # method-style fan-out -> teaching error


def test_handle_dot_switch_gives_top_level_hint() -> None:
    from composable_agents import flow, tool
    from composable_agents.define import DefineError

    @tool(effect="read", idempotent=True)
    def lk(t: str) -> dict:
        return {"x": 1}

    with pytest.raises(DefineError, match=r"switch is a top-level helper"):
        @flow
        def outer(t: str) -> object:
            hit = lk(t)
            return hit.switch(cases={})    # method-style branch on a Handle -> teaching error
```

(If `body.each(...)` currently produces a different exception type, adjust the `match` after Step 4 — but it MUST be a `DefineError` once fixed.)

- [ ] **Step 2: Run to confirm failure**

Run: `python -m pytest tests/test_define_frontend.py -k "top_level_hint" -v`
Expected: FAIL — `FlowDef.body.each` raises a generic `AttributeError`; `Handle.switch` raises the generic "Handle attribute access is not runtime data" `AttributeError`, neither a `DefineError` mentioning the top-level helper.

- [ ] **Step 3: Add the shared helper-name set** near `define.py:69`:

```python
_CONTROL_HELPERS = {"cond", "switch", "each", "reschedule"}
# Names that are top-level authoring helpers, never methods on a Handle/FlowDef.
# Used to turn `flow.each(...)` / `handle.switch(...)` into a teaching DefineError.
_TOP_LEVEL_HELPERS = _CONTROL_HELPERS | {"par", "seq", "map_n"}


def _top_level_helper_error(owner_label: str, name: str, source) -> "DefineError":
    return DefineError(
        f"{name} is a top-level helper, not a method"
        f"{_source_suffix(source)}; call {name}(...) and pass {owner_label} as an argument "
        f"(e.g. each(body, items) / switch(selector, subject, cases=...)), "
        f"not {owner_label}.{name}(...)."
    )
```

- [ ] **Step 4: Special-case in `Handle.__getattr__`** (`define.py:364-368`) — check helper names first:

```python
def __getattr__(self, name: str) -> object:
    if name in _TOP_LEVEL_HELPERS:
        raise _top_level_helper_error(self.label, name, self.source)
    raise AttributeError(
        f"Handle attribute access is not runtime data{_source_suffix(self.source)}; "
        f"got {self.label}.{name}. Use {self.label}[{name!r}] for std.pluck."
    )
```

- [ ] **Step 5: Add `FlowDef.__getattr__`** (`define.py`, in `class FlowDef` ~line 408). FlowDef currently has no `__getattr__`, so add one that only intercepts helper names and otherwise defers to normal attribute errors:

```python
def __getattr__(self, name: str) -> object:
    # __getattr__ only fires for genuinely-missing attributes.
    if name in _TOP_LEVEL_HELPERS:
        raise _top_level_helper_error(self.name, name, getattr(self, "source", None))
    raise AttributeError(f"{type(self).__name__!r} object has no attribute {name!r}")
```

(Confirm `FlowDef` has a `.name` and an optional `.source`/span attribute in Step 1-style reading; if the span attribute differs, pass the correct one. Guard against recursion: `__getattr__` must not reference an attribute that itself routes back through `__getattr__` — use `getattr(self, "source", None)` defensively.)

- [ ] **Step 6: Run the tests + the existing handle-attr test**

Run: `python -m pytest tests/test_define_frontend.py -v`
Expected: PASS, including the pre-existing `test` at line ~480 (`Handle attribute access ... Use source['foo']`) — a non-helper name like `foo` must still give the original pluck hint, so verify that test is unaffected.

- [ ] **Step 7: Gates + commit**

```bash
git add composable_agents/define.py tests/test_define_frontend.py
ruff check composable_agents && uv run mypy --strict composable_agents
git commit -m "fix(define): flow.each / handle.switch raise a DefineError pointing to the top-level helper"
```

---

## Self-review

- **Spec coverage (§6 of the design):** pure-arity raw `TypeError` → `DefineError` with merge fix → Task 1; misleading `flow.each(...)` "unregistered callable" → `DefineError` naming the top-level helper, on both `Handle` and `FlowDef` → Task 2; messages match the existing `DefineError` + `_source_suffix` + `fix` house style → both tasks; covered by unit tests in `tests/test_define_frontend.py` → both tasks.
- **Placeholder scan:** Task 1 Step 5 and Task 2 Steps 3-5 contain the exact new code; the only "read first" instructions (Step 1, the source-span accessor, FlowDef's span attribute) are explicit verification steps, not deferred work. Task 1 Step 7 (`Tool.__call__`) is a bounded conditional check with a defined outcome.
- **Type consistency:** `_TOP_LEVEL_HELPERS` and `_top_level_helper_error(owner_label, name, source)` are defined once (Task 2 Step 3) and called identically from `Handle.__getattr__` and `FlowDef.__getattr__`. `apply_if_authoring(self, args, kwargs)` is called with the widened `args` tuple from `Pure.__call__` (Task 1 Step 4) matching its existing `(fn, args, kwargs)` signature.
