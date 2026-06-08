# Composable Prompts via Registered Renderers — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a `Brain`'s system prompt be computed by a **registered renderer** (a name-addressed pure `Context -> str`, mirroring registered pure functions) reading a per-invoke projected `Context`, while `Brain.system` stays a `str` and only strings (`system` + `system_render`) ever enter the deploy artifact.

**Architecture:** A renderer is registered in `Registry` exactly like a pure (source-hashed for §6.4 drift). `Brain` gains a string `system_render` naming a renderer. A pure helper `rendered_brain_for(brain, value)` projects a `Context` from the invoke value and, when a renderer is named, returns a derived `Brain` whose `system` is the rendered string — wired into the one real LLM site, the `invokeBrain` activity (`activities.py:157`). The `Fragment` ADT (`Reader`/string-monoid combinators) is authoring sugar used *inside* a registered renderer function. Deploy hashing stays string-only and golden-stable via conditional-key inclusion.

**Tech Stack:** Python 3, pytest, `dataclasses`, `inspect`-based source hashing.

**Design spec:** `docs/design/prompt-fragments.md`. **Codex-reviewed:** the projected `Context` does NOT exist in the runtime today; this plan builds it (gap #6). Fragments stay local authoring sugar; the registered+hashed unit is the function (gaps #7/#8).

---

### Task 1: `Brain.system_render` (additive string field)

**Files:**
- Modify: `composable_agents/dotctx.py:34–71` (Brain field + `__init__`), `:106–146` (`brain_from_settings`)
- Test: `tests/test_prompt_renderers.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_prompt_renderers.py
from composable_agents.dotctx import Brain, brain_from_settings


def test_brain_defaults_system_render_none() -> None:
    b = Brain(name="b", model="m", system="hi")
    assert b.system == "hi"
    assert b.system_render is None


def test_brain_carries_system_render() -> None:
    b = Brain(name="b", model="m", system_render="b.system.v1")
    assert b.system == ""
    assert b.system_render == "b.system.v1"


def test_brain_from_settings_parses_system_render() -> None:
    b = brain_from_settings({"name": "b", "model": "m", "system_render": "r1"})
    assert b.system_render == "r1"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_prompt_renderers.py -v`
Expected: FAIL — `TypeError: __init__() got an unexpected keyword argument 'system_render'`

- [ ] **Step 3: Write minimal implementation**

In `dotctx.py`, add the field to the class body (after `context_scope`):

```python
    system_render: Optional[str] = None   # registered renderer name (a string); None => use `system`
```

Add the parameter to `__init__` (after `context_scope: ContextScope = ContextScope.LOCAL`):

```python
        system_render: Optional[str] = None,
```

And inside `__init__`, after the existing `object.__setattr__` calls:

```python
        object.__setattr__(self, "system_render", system_render)
```

In `brain_from_settings`, add to the `Brain(...)` construction:

```python
        system_render=settings.get("system_render") or settings.get("systemRender"),
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_prompt_renderers.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add composable_agents/dotctx.py tests/test_prompt_renderers.py
git commit -m "feat(dotctx): add Brain.system_render (renderer name)"
```

---

### Task 2: Renderer registration in `Registry` (mirror pures)

**Files:**
- Modify: `composable_agents/registry.py`
- Test: `tests/test_renderer_registry.py`

Mirror the pure path verbatim (`registry.py:22–26, 29–36, 61–80`): a `RendererEntry`, a `renderers` dict, `register_renderer`/`get_renderer`/`renderer_source_hash_of`, source-hashed with the existing `_source_hash`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_renderer_registry.py
import pytest
from composable_agents.registry import Registry


def _r(ctx):  # a renderer: Context -> str
    return f"hi {ctx.get('who','')}"


def test_register_and_get_renderer() -> None:
    reg = Registry()
    reg.register_renderer("greet.v1", _r)
    assert reg.get_renderer("greet.v1")({"who": "ada"}) == "hi ada"


def test_renderer_source_hash_is_pinned_and_stable() -> None:
    reg = Registry()
    reg.register_renderer("greet.v1", _r)
    h = reg.renderer_source_hash_of("greet.v1")
    assert h.startswith("renderer:")
    reg2 = Registry()
    reg2.register_renderer("greet.v1", _r)
    assert reg2.renderer_source_hash_of("greet.v1") == h


def test_collision_on_different_fn_raises() -> None:
    reg = Registry()
    reg.register_renderer("greet.v1", _r)
    with pytest.raises(ValueError):
        reg.register_renderer("greet.v1", lambda ctx: "other")


def test_unknown_renderer_raises() -> None:
    with pytest.raises(KeyError):
        Registry().get_renderer("nope")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_renderer_registry.py -v`
Expected: FAIL — `AttributeError: 'Registry' object has no attribute 'register_renderer'`

- [ ] **Step 3: Write minimal implementation**

In `registry.py`, add a `RendererEntry` next to `PureEntry`:

```python
@dataclass(frozen=True)
class RendererEntry:
    name: str
    fn: Callable[[Mapping[str, Any]], str]
    source_hash: str
```

Add `from collections.abc import Mapping` and `from typing import Any` if not present. In `Registry.__init__`, add the dict:

```python
        self.renderers: dict[str, RendererEntry] = {}
```

Add the methods (mirroring `register_pure`/`get_pure`/`source_hash_of`, reusing `_source_hash` with a `renderer:` prefix):

```python
    def register_renderer(self, name: str, fn: Callable[[Mapping[str, Any]], str]) -> RendererEntry:
        if name in self.renderers and self.renderers[name].fn is not fn:
            raise ValueError(f"renderer name already registered to a different fn: {name!r}")
        entry = RendererEntry(name=name, fn=fn, source_hash=_source_hash(fn).replace("pure:", "renderer:", 1))
        self.renderers[name] = entry
        return entry

    def get_renderer(self, name: str) -> Callable[[Mapping[str, Any]], str]:
        try:
            return self.renderers[name].fn
        except KeyError as e:
            raise KeyError(f"unknown renderer {name!r}; register it with @renderer({name!r})") from e

    def renderer_source_hash_of(self, name: str) -> str:
        return self.renderers[name].source_hash
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_renderer_registry.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add composable_agents/registry.py tests/test_renderer_registry.py
git commit -m "feat(registry): renderer registration mirroring pures (source-hashed)"
```

---

### Task 3: `prompt.py` — `Context`, projection, `render_system`, `rendered_brain_for`

**Files:**
- Create: `composable_agents/prompt.py`
- Test: `tests/test_prompt_renderers.py`

`rendered_brain_for` is the pure seam wired into the activity in Task 4 — testable with no Temporal/`_CTX`.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_prompt_renderers.py
from composable_agents.dotctx import Brain
from composable_agents.prompt import project_context, render_system, rendered_brain_for, register_renderer


def test_project_context_unwraps_mapping_value() -> None:
    assert project_context({"input": 1, "trace": []}) == {"input": 1, "trace": []}
    assert project_context(7) == {"value": 7}


def test_render_system_without_renderer_returns_literal() -> None:
    b = Brain(name="b", model="m", system="literal")
    assert render_system(b, {"value": 1}) == "literal"


def test_rendered_brain_for_applies_registered_renderer() -> None:
    register_renderer("greet.v2", lambda ctx: f"Hello {ctx['who']}")
    b = Brain(name="b", model="m", system="ignored", system_render="greet.v2")
    out = rendered_brain_for(b, {"who": "ada"})
    assert out.system == "Hello ada"
    assert out.system_render is None          # rendered brain carries no renderer
    assert out.name == "b" and out.model == "m"


def test_rendered_brain_for_passes_plain_brain_through_unchanged() -> None:
    b = Brain(name="b", model="m", system="literal")
    assert rendered_brain_for(b, {"value": 1}) is b
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_prompt_renderers.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'composable_agents.prompt'`

- [ ] **Step 3: Write minimal implementation**

```python
# composable_agents/prompt.py
"""Composable prompts via registered renderers (design: docs/design/prompt-fragments.md).

A renderer is a pure ``Context -> str`` registered by name (like a pure). A
Brain names one via ``system_render``; ``rendered_brain_for`` projects a Context
from the invoke value and returns a derived Brain whose ``system`` is the
rendered string. ``Context`` is the v1 projection: the invoke value if it is a
mapping (the agent-loop payload ``{"input":..., "trace":...}`` already is one),
else ``{"value": value}``. Richer ContextScope/session projection is deferred.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Callable

from .dotctx import Brain
from .registry import DEFAULT_REGISTRY

Context = Mapping[str, Any]


def register_renderer(name: str, fn: Callable[[Context], str]):
    return DEFAULT_REGISTRY.register_renderer(name, fn)


def get_renderer(name: str) -> Callable[[Context], str]:
    return DEFAULT_REGISTRY.get_renderer(name)


def renderer(name: str):
    """Decorator: register a top-level ``def f(ctx) -> str`` as a renderer. Its
    source is what gets hashed for §6.4 drift, exactly like ``@pure``."""
    def deco(fn: Callable[[Context], str]) -> Callable[[Context], str]:
        register_renderer(name, fn)
        return fn
    return deco


def project_context(value: Any) -> dict[str, Any]:
    """v1 Context projection at the invoke boundary."""
    return dict(value) if isinstance(value, Mapping) else {"value": value}


def render_system(brain: Brain, ctx: Context) -> str:
    if brain.system_render is not None:
        return DEFAULT_REGISTRY.get_renderer(brain.system_render)(ctx)
    return brain.system


def _with_rendered_system(brain: Brain, system: str) -> Brain:
    return Brain(
        name=brain.name, model=brain.model, system=system,
        reply_schema=brain.reply_schema, tools=brain.tools,
        temperature=brain.temperature, max_rounds=brain.max_rounds,
        is_agent=brain.is_agent, sub_contract=brain.sub_contract,
        context_scope=brain.context_scope, system_render=None,
    )


def rendered_brain_for(brain: Brain, value: Any) -> Brain:
    """The invoke seam: a no-renderer brain passes through identically; a
    renderer-bearing brain becomes a derived brain with the rendered system."""
    if brain.system_render is None:
        return brain
    return _with_rendered_system(brain, render_system(brain, project_context(value)))


__all__ = [
    "Context", "register_renderer", "get_renderer", "renderer",
    "project_context", "render_system", "rendered_brain_for",
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_prompt_renderers.py -v`
Expected: PASS (7 passed total in the file)

- [ ] **Step 5: Commit**

```bash
git add composable_agents/prompt.py tests/test_prompt_renderers.py
git commit -m "feat(prompt): render_system + rendered_brain_for + Context projection"
```

---

### Task 4: Wire `rendered_brain_for` into the `invokeBrain` activity

**Files:**
- Modify: `composable_agents/execution/activities.py:157–162`
- Test: `tests/test_prompt_renderers.py`

The local `InMemoryEnv.invoke_brain` (`interpreter.py:559`) is a test double that never reads `brain.system`, so it needs no change. The one real LLM site is the activity.

- [ ] **Step 1: Write the failing test (activity renders before calling the LLM)**

```python
# append to tests/test_prompt_renderers.py
import asyncio
from composable_agents.execution import activities as act
from composable_agents.dotctx import register_brain
from composable_agents.prompt import register_renderer


def test_invoke_brain_renders_system_before_llm() -> None:
    register_renderer("inv.sys.v1", lambda ctx: f"sys:{ctx['input']}")
    register_brain(Brain(name="inv.brain", model="m", system_render="inv.sys.v1"))

    captured: dict = {}

    async def fake_llm(brain, value):
        captured["system"] = brain.system
        captured["system_render"] = brain.system_render
        return {"ok": True}

    prev = act._CTX.llm
    act._CTX.llm = fake_llm
    try:
        out = asyncio.run(act.invokeBrain(act.InvokeBrainInput(brain="inv.brain", value={"input": 42})))
    finally:
        act._CTX.llm = prev

    assert out == {"ok": True}
    assert captured["system"] == "sys:42"
    assert captured["system_render"] is None
```

> If `InvokeBrainInput` requires `cid`, pass `cid="c1"`. Confirm its fields at `activities.py:104`.

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_prompt_renderers.py::test_invoke_brain_renders_system_before_llm -v`
Expected: FAIL — the fake LLM sees the unrendered brain (`captured["system"] == ""`, `system_render == "inv.sys.v1"`).

- [ ] **Step 3: Write minimal implementation**

In `activities.py`, import the seam near the top:

```python
from ..prompt import rendered_brain_for
```

Change the `invokeBrain` body (`:159–162`) from:

```python
    brain = _registry().get_brain(inp.brain)
    return await _CTX.llm(brain, inp.value)
```

to:

```python
    brain = rendered_brain_for(_registry().get_brain(inp.brain), inp.value)
    return await _CTX.llm(brain, inp.value)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_prompt_renderers.py -v`
Expected: PASS (8 passed). Existing no-renderer brains are unaffected — `rendered_brain_for` returns them unchanged.

- [ ] **Step 5: Commit**

```bash
git add composable_agents/execution/activities.py tests/test_prompt_renderers.py
git commit -m "feat(activities): invokeBrain renders system_render before the LLM call"
```

---

### Task 5: The `Fragment` ADT (authoring sugar)

**Files:**
- Modify: `composable_agents/prompt.py`
- Test: `tests/test_fragments.py`

A closed union of frozen dataclasses, each with a concrete `render(ctx) -> str` — no `typing.Protocol`/`isinstance` (codex #9). Used *inside* a registered renderer function.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_fragments.py
from composable_agents.prompt import Lift, Ask, Concat, Under, Map, fragments


def test_lift_is_constant() -> None:
    assert Lift("x").render({"any": 1}) == "x"


def test_ask_reads_field_with_formatter() -> None:
    assert Ask("who", fmt=lambda v: f"[{v}]").render({"who": "ada"}) == "[ada]"
    assert Ask("missing").render({}) == ""           # default "" then str("") == ""


def test_concat_is_string_monoid() -> None:
    f = fragments("a", Ask("b"), "c")                # str auto-lifts
    assert f.render({"b": "B"}) == "aBc"
    assert Concat(()).render({}) == ""               # identity


def test_under_contramaps_the_environment() -> None:
    inner = Ask("name")
    f = Under(lambda c: c["user"], inner)
    assert f.render({"user": {"name": "ada"}}) == "ada"


def test_map_post_processes_output() -> None:
    assert Map(Lift("hi"), str.upper).render({}) == "HI"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_fragments.py -v`
Expected: FAIL — `ImportError: cannot import name 'Lift'`

- [ ] **Step 3: Write minimal implementation**

```python
# append to composable_agents/prompt.py
from dataclasses import dataclass


@dataclass(frozen=True)
class Lift:
    text: str
    def render(self, ctx: Context) -> str: return self.text


@dataclass(frozen=True)
class Ask:
    key: str
    fmt: Callable[[Any], str] = str
    def render(self, ctx: Context) -> str: return self.fmt(ctx.get(self.key, ""))


@dataclass(frozen=True)
class Concat:
    parts: tuple[Any, ...]                            # tuple[Fragment, ...]
    def render(self, ctx: Context) -> str: return "".join(p.render(ctx) for p in self.parts)


@dataclass(frozen=True)
class Under:
    project: Callable[[Context], Context]
    body: Any                                         # Fragment
    def render(self, ctx: Context) -> str: return self.body.render(self.project(ctx))


@dataclass(frozen=True)
class Map:
    body: Any                                         # Fragment
    fn: Callable[[str], str]
    def render(self, ctx: Context) -> str: return self.fn(self.body.render(ctx))


_FRAGMENT_TYPES = (Lift, Ask, Concat, Under, Map)


def fragments(*parts: Any) -> Concat:
    return Concat(tuple(p if isinstance(p, _FRAGMENT_TYPES) else Lift(p) for p in parts))
```

Extend `__all__` with `"Lift", "Ask", "Concat", "Under", "Map", "fragments"`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_fragments.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add composable_agents/prompt.py tests/test_fragments.py
git commit -m "feat(prompt): Fragment ADT (Reader/string-monoid authoring combinators)"
```

---

### Task 6: End-to-end — a Fragment-backed renderer on a Brain

**Files:**
- Test: `tests/test_prompt_renderers.py`

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_prompt_renderers.py
from composable_agents.prompt import renderer, fragments, Ask, rendered_brain_for


def test_fragment_backed_renderer_end_to_end() -> None:
    @renderer("research.system.v1")
    def research_system(ctx):
        return fragments(
            "You are a careful research agent.\n",
            Ask("persona", fmt=lambda p: f"Persona: {p}"),
        ).render(ctx)

    b = Brain(name="researcher", model="m", system_render="research.system.v1")
    out = rendered_brain_for(b, {"persona": "skeptic"})
    assert out.system == "You are a careful research agent.\nPersona: skeptic"
```

- [ ] **Step 2: Run test to verify it fails, then passes**

Run: `pytest tests/test_prompt_renderers.py::test_fragment_backed_renderer_end_to_end -v`
Expected: PASS immediately (all pieces exist from Tasks 3 + 5). If it fails, the `@renderer` registration or `fragments` lowering is wrong — fix before continuing.

- [ ] **Step 3: Commit**

```bash
git add tests/test_prompt_renderers.py
git commit -m "test(prompt): fragment-backed renderer end-to-end on a Brain"
```

---

### Task 7: Deploy artifact + drift parity (golden-stable)

**Files:**
- Modify: `composable_agents/deploy.py:138–149` (`_brain_identity`), `:120–124` + `:182–197` (`_renderer_source_hashes` + `artifact_components`)
- Test: `tests/test_renderer_deploy.py`

Critical: **add keys only when present**, so existing no-renderer brains hash byte-identically (golden corpus must not move).

- [ ] **Step 1: Confirm golden is green before touching deploy**

Run: `pytest tests/golden/test_golden.py -q`
Expected: PASS. This is the gate Task 7 must not break.

- [ ] **Step 2: Write the failing test**

```python
# tests/test_renderer_deploy.py
from composable_agents.deploy import _brain_identity, _renderer_source_hashes
from composable_agents.dotctx import Brain, register_brain
from composable_agents.prompt import register_renderer
from composable_agents.dsl import think


def test_brain_identity_omits_system_render_when_absent() -> None:
    register_brain(Brain(name="plain.b", model="m", system="s"))
    ident = _brain_identity("plain.b")
    assert "systemRender" not in ident          # no new key => golden unchanged


def test_brain_identity_includes_system_render_when_present() -> None:
    register_renderer("dep.r.v1", lambda ctx: "x")
    register_brain(Brain(name="rendered.b", model="m", system_render="dep.r.v1"))
    ident = _brain_identity("rendered.b")
    assert ident["systemRender"] == "dep.r.v1"


def test_renderer_source_hashes_pins_referenced_renderers() -> None:
    register_renderer("dep.r.v2", lambda ctx: "y")
    register_brain(Brain(name="rb2", model="m", system_render="dep.r.v2"))
    flow = think("rb2")
    hashes = _renderer_source_hashes(flow)
    assert hashes["dep.r.v2"].startswith("renderer:")
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/test_renderer_deploy.py -v`
Expected: FAIL — `ImportError: cannot import name '_renderer_source_hashes'` (and `systemRender` missing).

- [ ] **Step 4: Write minimal implementation**

In `deploy.py`, make `_brain_identity` add the key only when set (`:144–149`):

```python
    ident = {
        "name": brain.name,
        "model": brain.model,
        "system": brain.system,
        "replySchema": brain.reply_schema,
        "tools": list(brain.tools),
    }
    if brain.system_render is not None:
        ident["systemRender"] = brain.system_render
    return ident
```

Add a `_renderer_source_hashes` mirroring `_pure_source_hashes` (`:120–124`), keyed by the renderer names referenced via brains:

```python
def _renderer_source_hashes(flow: Node) -> dict[str, str]:
    out: dict[str, str] = {}
    for name in _referenced_brains(flow):
        try:
            render_name = get_brain(name).system_render
        except KeyError:
            continue
        if render_name and render_name in DEFAULT_REGISTRY.renderers:
            out[render_name] = DEFAULT_REGISTRY.renderer_source_hash_of(render_name)
    return out
```

Import `DEFAULT_REGISTRY` and `get_brain` if not already imported. In `artifact_components`, add the block **only when non-empty** (so existing artifacts are byte-identical):

```python
        components = { ...existing dict... }
        renderer_hashes = _renderer_source_hashes(self.flow)
        if renderer_hashes:
            components["rendererSourceHashes"] = renderer_hashes
        return components
```

(If `artifact_components` currently `return {...}` directly, bind it to `components` first, then conditionally add, then `return components`.)

- [ ] **Step 5: Run tests + golden gate**

Run: `pytest tests/test_renderer_deploy.py -v && pytest tests/golden/test_golden.py -q`
Expected: PASS both. Golden must be unchanged — no-renderer brains add no keys.

- [ ] **Step 6: Commit**

```bash
git add composable_agents/deploy.py tests/test_renderer_deploy.py
git commit -m "feat(deploy): pin system_render + renderer source hashes (golden-stable, additive)"
```

---

### Task 8: Full-suite verification

- [ ] **Step 1: Run the whole suite**

Run: `pytest -q`
Expected: PASS. Golden corpus unchanged; new renderer tests green.

- [ ] **Step 2: Confirm the public surface**

Run: `python -c "from composable_agents.prompt import render_system, rendered_brain_for, renderer, fragments, Ask; from composable_agents.registry import DEFAULT_REGISTRY; print('ok')"`
Expected: `ok`

- [ ] **Step 3: Commit (if fixups were needed)**

```bash
git add -A && git commit -m "test: full-suite green for prompt renderers" || echo "nothing to commit"
```

---

## Self-Review

- **Spec coverage:** registered renderer reading projected Context (Tasks 2–4), `Brain.system` stays `str` + `system_render` string (Task 1), the projection path that didn't exist (Task 3 `project_context`), Fragment ADT as authoring sugar (Task 5), deploy/drift parity with string-only artifact + golden stability (Task 7), determinism via source-hash registration like pures (Tasks 2 + 7). The §6.4 drift *diff at replay* reuses the existing `verifyPures`-style path conceptually; a `verifyRenderers` activity is a follow-on (noted, not built) — acceptable, since the artifact already pins the hashes.
- **Placeholders:** none — every code step shows complete code; the two "confirm the field at activities.py:104 / shape of artifact_components" notes are verification cues, not deferred work.
- **Type consistency:** `Context`, `register_renderer`/`get_renderer`/`renderer`, `project_context`, `render_system`, `rendered_brain_for` defined in Task 3 and reused unchanged in Tasks 4/6; `RendererEntry`/`register_renderer`/`renderer_source_hash_of` defined in Task 2 and consumed in Task 7; `_with_rendered_system` builds a `Brain` with the exact field set from Task 1 (including `system_render=None`).
