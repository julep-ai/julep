# mem-mcp Adoption Phase 1: LLM + Prompt Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make composable-agents' LLM and prompt layers able to faithfully run mem-mcp's single-shot structured reasoners: reasoning-effort passthrough, mem-mcp model-slug compatibility, recorded (not silent) response_format fallback, bounded structured-output retries, and Yglu-evaluated `settings.yaml` with an explicit env binding.

**Architecture:** All changes sit in the pure core (`dotctx.py`, new `model_slugs.py`, new `dotctx_yglu.py`), the provider seam (`execution/llm.py`, `execution/llm_result.py`), and `deploy.py`'s reasoner identity. `freeze.py` collects only reasoner *names* and tool keys, but `deploy.py:_reasoner_identity()` (line 159) hashes reasoner config into the artifact hash — new fields MUST enter it, following its existing omit-when-unset convention so pre-existing artifacts hash identically (Task 2). Yglu is a new optional extra mirroring how `[dotctx]` gates jinja2.

**Tech Stack:** Python 3.10+, any-llm (`reasoning_effort` param already exists: `Literal["none","minimal","low","medium","high","xhigh","max","auto"]`), yglu>=1.0 (new optional), PyYAML, pytest, mypy --strict, ruff.

## Global Constraints

- Run tests as `python -m pytest` (never bare `pytest`); type-check as `uv run mypy --strict composable_agents` (package only, not tests).
- New tests must not require temporal (`HAVE_TEMPORAL` off-job must stay green); nothing in this plan touches temporal.
- `yglu` must NOT become a required dependency — optional extra only, lazy import, hard error with install hint when needed (G-8: no silent fallback).
- Existing deploy goldens must be byte-for-byte unchanged (verify in Task 2).
- New `LlmCallMeta.to_attrs()` keys are emitted only when non-default, so existing projection/Langfuse attr snapshots don't change.
- mem-mcp effort levels are `{"minimal","low","medium","high","xhigh","none"}`; CA accepts those plus any-llm's `"max"`. `"auto"` is rejected (it's any-llm's implicit default, not a declarable level).
- Commit after every task; message prefix `feat(phase1):` / `fix(phase1):`.

## Reference: mem-mcp semantics being mirrored

- Slug parsing (`memory_store_utils/model_preferences.py`): `rsplit("@", 1)`, suffix only recognized if in the level set; `provider:model` and `provider/model` both accepted; special prefixes `vertex_ai/ → vertexai:`, `google/|gemini/ → gemini:`, bare slug → default provider.
- Reasoning temperature rule (`get_temperature_for_reasoning`): when effort is set and ≠ `"none"`, temperature is overridden (mem-mcp forces 1.0; we *omit* temperature instead — Anthropic defaults to 1.0 with thinking, OpenAI reasoning models reject the param entirely; omission is the provider-safe equivalent).
- Yglu env gating (`dotctx/loader.py:_yglu_env`): yglu reads `$env` from `os.environ` gated by `YGLU_ENABLE_ENV`. CA replaces ambient reads with an explicit mapping (freeze-determinism) by swapping `os.environ` inside a context manager — CLI-time only, documented as not thread-safe.

---

### Task 1: `model_slugs.py` — pure slug/effort normalization

**Files:**
- Create: `composable_agents/model_slugs.py`
- Test: `tests/test_model_slugs.py`

**Interfaces:**
- Produces: `EFFORT_LEVELS: frozenset[str]`; `@dataclass(frozen=True) ModelSlug(model: str, reasoning_effort: Optional[str], raw: str)`; `normalize_model_slug(raw: str) -> ModelSlug`. Task 3 calls `normalize_model_slug` from both settings loaders; Task 4 validates against `EFFORT_LEVELS`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_model_slugs.py
import pytest
from composable_agents.model_slugs import ModelSlug, normalize_model_slug


@pytest.mark.parametrize(
    "raw,model,effort",
    [
        ("openai/gpt-5.4-nano@medium", "openai:gpt-5.4-nano", "medium"),
        ("anthropic:claude-sonnet-4-6@high", "anthropic:claude-sonnet-4-6", "high"),
        ("openrouter:inception/mercury-2", "openrouter:inception/mercury-2", None),
        ("openrouter/inception/mercury-2@low", "openrouter:inception/mercury-2", "low"),
        ("openai/gpt-5.4-mini@none", "openai:gpt-5.4-mini", "none"),
        ("claude-opus-4-8", "claude-opus-4-8", None),          # bare slug untouched
        ("vertex_ai/gemini-2.5-pro", "vertexai:gemini-2.5-pro", None),
        ("google/gemini-2.5-flash", "gemini:gemini-2.5-flash", None),
        ("gemini/gemini-2.5-flash@xhigh", "gemini:gemini-2.5-flash", "xhigh"),
        ("openai:gpt-4o", "openai:gpt-4o", None),               # canonical passes through
        ("model@vintage", "model@vintage", None),               # unknown suffix is part of the name
        ("  openai/gpt-4o@LOW  ", "openai:gpt-4o", "low"),      # trim + case-fold suffix
    ],
)
def test_normalize(raw: str, model: str, effort: str | None) -> None:
    out = normalize_model_slug(raw)
    assert out == ModelSlug(model=model, reasoning_effort=effort, raw=raw)


def test_empty_raises() -> None:
    with pytest.raises(ValueError):
        normalize_model_slug("   ")
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_model_slugs.py -v`
Expected: FAIL — `ModuleNotFoundError: composable_agents.model_slugs`

- [ ] **Step 3: Implement**

```python
# composable_agents/model_slugs.py
"""Normalize mem-mcp-style model slugs into CA's canonical ``provider:model``.

Accepted inputs: ``provider:model``, ``provider/model``, bare model names, each
optionally suffixed ``@<effort>``. The effort suffix is only recognized when it
is a known level — ``model@vintage`` stays a model name. Pure module: no IO.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# mem-mcp's levels plus any-llm's "max". "auto" is any-llm's implicit default
# and deliberately not declarable.
EFFORT_LEVELS: frozenset[str] = frozenset(
    {"none", "minimal", "low", "medium", "high", "xhigh", "max"}
)

_PREFIX_MAP = {"vertex_ai": "vertexai", "google": "gemini", "gemini": "gemini"}


@dataclass(frozen=True)
class ModelSlug:
    model: str
    reasoning_effort: Optional[str]
    raw: str


def normalize_model_slug(raw: str) -> ModelSlug:
    trimmed = raw.strip()
    if not trimmed:
        raise ValueError("model slug is empty")

    effort: Optional[str] = None
    if "@" in trimmed:
        candidate, suffix = trimmed.rsplit("@", 1)
        if suffix.strip().lower() in EFFORT_LEVELS:
            trimmed, effort = candidate.strip(), suffix.strip().lower()

    colon, slash = trimmed.find(":"), trimmed.find("/")
    if colon == -1 and slash == -1:
        return ModelSlug(model=trimmed, reasoning_effort=effort, raw=raw)
    if colon != -1 and (slash == -1 or colon < slash):
        provider, rest = trimmed.split(":", 1)
    else:
        provider, rest = trimmed.split("/", 1)
    provider = _PREFIX_MAP.get(provider, provider)
    return ModelSlug(model=f"{provider}:{rest}", reasoning_effort=effort, raw=raw)


__all__ = ["EFFORT_LEVELS", "ModelSlug", "normalize_model_slug"]
```

- [ ] **Step 4: Run tests, then gates**

Run: `python -m pytest tests/test_model_slugs.py -v` → PASS
Run: `uv run mypy --strict composable_agents && ruff check composable_agents` → clean

- [ ] **Step 5: Commit** — `git add composable_agents/model_slugs.py tests/test_model_slugs.py && git commit -m "feat(phase1): pure model-slug/effort normalization"`

---

### Task 2: `Reasoner.reasoning_effort` + `Reasoner.output_retries` fields

**Files:**
- Modify: `composable_agents/dotctx.py:135-189` (dataclass + custom `__init__`)
- Modify: `composable_agents/execution/llm.py:373-391` (`_with_model` copy-through)
- Modify: `composable_agents/deploy.py:159-179` (`_reasoner_identity` — new fields join the artifact hash, omit-when-unset)
- Test: `tests/test_reasoner_fields.py`

**Interfaces:**
- Produces: `Reasoner(reasoning_effort: Optional[str] = None, output_retries: int = 0)` keyword params, stored as frozen fields. Tasks 3–6 read `reasoner.reasoning_effort` / `reasoner.output_retries`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_reasoner_fields.py
from composable_agents.dotctx import Reasoner
from composable_agents.execution.llm import _with_model


def test_fields_default() -> None:
    r = Reasoner(name="t", model="openai:gpt-4o")
    assert r.reasoning_effort is None
    assert r.output_retries == 0


def test_with_model_carries_new_fields() -> None:
    r = Reasoner(name="t", model="openai:gpt-4o",
                 reasoning_effort="high", output_retries=2)
    moved = _with_model(r, "anthropic:claude-sonnet-4-6")
    assert moved.model == "anthropic:claude-sonnet-4-6"
    assert moved.reasoning_effort == "high"
    assert moved.output_retries == 2


def test_reasoner_identity_stable_on_defaults_and_moves_on_values() -> None:
    from composable_agents.deploy import _reasoner_identity
    from composable_agents.dotctx import DEFAULT_REGISTRY

    DEFAULT_REGISTRY.register_reasoner(Reasoner(name="ident-a", model="m"))
    DEFAULT_REGISTRY.register_reasoner(
        Reasoner(name="ident-b", model="m", reasoning_effort="low", output_retries=1))
    a, b = _reasoner_identity("ident-a"), _reasoner_identity("ident-b")
    assert "reasoningEffort" not in a and "outputRetries" not in a  # defaults: hash-stable
    assert b["reasoningEffort"] == "low" and b["outputRetries"] == 1
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_reasoner_fields.py -v`
Expected: FAIL — `TypeError: __init__() got an unexpected keyword argument 'reasoning_effort'`

- [ ] **Step 3: Implement**

In `composable_agents/dotctx.py`, add two field declarations after `max_tokens` (line 151):

```python
    max_tokens: Optional[int] = None      # forwarded to the provider call when set
    reasoning_effort: Optional[str] = None  # provider thinking effort (model_slugs.EFFORT_LEVELS)
    output_retries: int = 0               # re-asks when a schema'd reply fails to parse
```

Extend `__init__` — add keyword-only params after `reply` and two `__setattr__` lines at the end of the body:

```python
        *,
        reply: Any = _REPLY_UNSET,
        reasoning_effort: Optional[str] = None,
        output_retries: int = 0,
    ) -> None:
```

```python
        object.__setattr__(self, "max_tokens", max_tokens)
        object.__setattr__(self, "reasoning_effort", reasoning_effort)
        object.__setattr__(self, "output_retries", output_retries)
```

In `composable_agents/execution/llm.py` `_with_model` (line 377), add to the `Reasoner(...)` construction:

```python
        reply=reasoner.reply_schema,
        reasoning_effort=reasoner.reasoning_effort,
        output_retries=reasoner.output_retries,
    )
```

In `composable_agents/deploy.py` `_reasoner_identity` (line 159), extend the omit-when-unset block — same convention as the `maxTokens` line above it:

```python
    if reasoner.reasoning_effort is not None:
        ident["reasoningEffort"] = reasoner.reasoning_effort
    if reasoner.output_retries:
        ident["outputRetries"] = reasoner.output_retries
```

- [ ] **Step 4: Run tests, full suite, and golden check**

Run: `python -m pytest tests/test_reasoner_fields.py -v` → PASS
Run: `python -m pytest` → full suite PASS. Freeze/deploy golden tests (`tests/` matching `freeze`/`golden`/`deploy`) prove hashes unmoved — `freeze.py:250-253` only reads reasoner *names* and `.tools`, so this must hold; investigate any golden diff before proceeding.
Run: `uv run mypy --strict composable_agents && ruff check composable_agents` → clean

- [ ] **Step 5: Commit** — `git commit -am "feat(phase1): Reasoner.reasoning_effort + output_retries fields"`

---

### Task 3: Settings mapping in both dotctx loaders

**Files:**
- Modify: `composable_agents/dotctx.py:220-263` (`reasoner_from_settings`)
- Modify: `composable_agents/dotctx_rich.py:47-61` (`_ALLOWED_SETTINGS`) and `:662-675` (Reasoner construction; drop the `# @effort suffixes pass through untouched` comment — it becomes false)
- Test: `tests/test_settings_effort.py`

**Interfaces:**
- Consumes: `normalize_model_slug`, `EFFORT_LEVELS` (Task 1); `Reasoner` fields (Task 2).
- Produces: both loaders emit Reasoners with canonical `model`, populated `reasoning_effort` (explicit `reasoning_effort:` key wins over `@suffix`), and `output_retries`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_settings_effort.py
import pytest
from composable_agents.dotctx import reasoner_from_settings


def test_suffix_extracted_and_model_canonicalized() -> None:
    r = reasoner_from_settings(
        {"model": "openai/gpt-5.4-nano@medium"}, name="t1")
    assert r.model == "openai:gpt-5.4-nano"
    assert r.reasoning_effort == "medium"


def test_explicit_key_wins_over_suffix() -> None:
    r = reasoner_from_settings(
        {"model": "openai/gpt-5.4-nano@medium", "reasoning_effort": "high"},
        name="t2")
    assert r.reasoning_effort == "high"


def test_invalid_effort_key_raises() -> None:
    with pytest.raises(ValueError, match="reasoning_effort"):
        reasoner_from_settings(
            {"model": "openai:gpt-4o", "reasoning_effort": "auto"}, name="t3")


def test_output_retries_mapped() -> None:
    r = reasoner_from_settings(
        {"model": "openai:gpt-4o", "output_retries": 2}, name="t4")
    assert r.output_retries == 2
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_settings_effort.py -v`
Expected: FAIL — model keeps `@medium`, `reasoning_effort` is None.

- [ ] **Step 3: Implement**

In `dotctx.py`, import at module top: `from .model_slugs import EFFORT_LEVELS, normalize_model_slug`. Add a shared helper above `reasoner_from_settings`:

```python
def _model_and_effort(settings: dict[str, Any]) -> tuple[str, Optional[str], int]:
    """Canonical model, effort (explicit key beats @suffix), output_retries."""
    slug = normalize_model_slug(str(settings.get("model", "claude-sonnet-4")))
    effort = settings.get("reasoning_effort") or settings.get("reasoningEffort")
    if effort is not None:
        effort = str(effort).strip().lower()
        if effort not in EFFORT_LEVELS:
            raise ValueError(
                f"reasoning_effort {effort!r} is not one of {sorted(EFFORT_LEVELS)}"
            )
    retries = int(settings.get("output_retries")
                  or settings.get("outputRetries") or 0)
    if retries < 0:
        raise ValueError("output_retries must be >= 0")
    return slug.model, (effort or slug.reasoning_effort), retries
```

In `reasoner_from_settings`, replace `model=settings.get("model", "claude-sonnet-4"),` with:

```python
    model, effort, output_retries = _model_and_effort(settings)
    reasoner = Reasoner(
        name=nm,
        model=model,
        ...
        reasoning_effort=effort,
        output_retries=output_retries,
    )
```

In `dotctx_rich.py`: add `"reasoning_effort"`, `"reasoningEffort"`, `"output_retries"`, `"outputRetries"` to `_ALLOWED_SETTINGS`; import `_model_and_effort` alongside the existing `from .dotctx import Reasoner, _sub_from`; in the rich Reasoner construction (line ~662) apply the same three-values pattern replacing `model=settings.get("model", "claude-sonnet-4")`.

- [ ] **Step 4: Run tests + gates**

Run: `python -m pytest tests/test_settings_effort.py tests/test_dotctx_rich.py tests/test_dotctx_reply.py -v` → PASS (rich tests confirm no allowed-keys regression)
Run: `python -m pytest && uv run mypy --strict composable_agents && ruff check composable_agents` → clean

- [ ] **Step 5: Commit** — `git commit -am "feat(phase1): settings map model@effort + reasoning_effort/output_retries in both loaders"`

---

### Task 4: Reasoning-effort passthrough in `complete_reasoner`

**Files:**
- Modify: `composable_agents/execution/llm.py:258-276` (the `call` closure)
- Test: `tests/test_llm_effort.py`

**Interfaces:**
- Consumes: `Reasoner.reasoning_effort` (Task 2).
- Produces: `acompletion(..., reasoning_effort=<level>)` when set; param absent when unset (any-llm's own `"auto"` default must not be disturbed). When effort is set and ≠ `"none"`, `temperature` is omitted (mem-mcp's reasoning-temperature rule, provider-safe form).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_llm_effort.py
import asyncio
from types import SimpleNamespace
from typing import Any

from composable_agents.dotctx import Reasoner
from composable_agents.execution.llm import complete_reasoner


def _completion(content: str = "ok") -> Any:
    msg = SimpleNamespace(content=content, parsed=None)
    return SimpleNamespace(choices=[SimpleNamespace(message=msg)],
                           usage=None, model="m")


def _run(reasoner: Reasoner) -> dict[str, Any]:
    seen: dict[str, Any] = {}

    async def fake_acompletion(**kwargs: Any) -> Any:
        seen.update(kwargs)
        return _completion()

    asyncio.run(complete_reasoner(reasoner, "hi", acompletion=fake_acompletion))
    return seen


def test_effort_forwarded_and_temperature_dropped() -> None:
    seen = _run(Reasoner(name="t", model="openai:gpt-4o",
                         temperature=0.2, reasoning_effort="high"))
    assert seen["reasoning_effort"] == "high"
    assert "temperature" not in seen


def test_effort_none_forwarded_temperature_kept() -> None:
    seen = _run(Reasoner(name="t", model="openai:gpt-4o",
                         temperature=0.2, reasoning_effort="none"))
    assert seen["reasoning_effort"] == "none"
    assert seen["temperature"] == 0.2


def test_unset_effort_not_sent() -> None:
    seen = _run(Reasoner(name="t", model="openai:gpt-4o", temperature=0.2))
    assert "reasoning_effort" not in seen
    assert seen["temperature"] == 0.2
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_llm_effort.py -v`
Expected: FAIL — `reasoning_effort` never in kwargs.

- [ ] **Step 3: Implement**

In the `call` closure (llm.py:271-274), replace the temperature/max_tokens block with:

```python
        effort = reasoner.reasoning_effort
        if effort is not None:
            kwargs["reasoning_effort"] = effort
        # Thinking modes reject or require fixed sampling params; omit
        # temperature whenever reasoning is actually enabled (mirrors mem-mcp's
        # get_temperature_for_reasoning, in provider-safe form).
        if reasoner.temperature is not None and (effort is None or effort == "none"):
            kwargs["temperature"] = reasoner.temperature
        if reasoner.max_tokens is not None:
            kwargs["max_tokens"] = reasoner.max_tokens
```

- [ ] **Step 4: Run tests + gates**

Run: `python -m pytest tests/test_llm_effort.py tests/test_llm.py tests/test_resilient_llm.py -v && uv run mypy --strict composable_agents && ruff check composable_agents` → PASS/clean

- [ ] **Step 5: Commit** — `git commit -am "feat(phase1): reasoning_effort passthrough to any-llm"`

---

### Task 5: Record the response_format fallback (kill the silent downgrade)

**Files:**
- Modify: `composable_agents/execution/llm.py:278-297` (`complete_reasoner` try/except + meta)
- Modify: `composable_agents/execution/llm_result.py:23-55` (`LlmCallMeta` + `to_attrs`)
- Test: `tests/test_llm_fallback_recorded.py`

**Interfaces:**
- Produces: `LlmCallMeta.response_format_fallback: str | None = None` (the exception `repr` that triggered the downgrade); `to_attrs()` emits `"llm.response_format_fallback"` only when set; a `logging.warning` on the `composable_agents.execution.llm` logger.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_llm_fallback_recorded.py
import asyncio
import logging
from types import SimpleNamespace
from typing import Any

import pytest

from composable_agents.dotctx import Reasoner
from composable_agents.execution.llm import complete_reasoner

SCHEMA = {"type": "object", "properties": {"x": {"type": "integer"}}}


def _completion(content: str) -> Any:
    msg = SimpleNamespace(content=content, parsed=None)
    return SimpleNamespace(choices=[SimpleNamespace(message=msg)],
                           usage=None, model="m")


def test_fallback_recorded_and_logged(caplog: pytest.LogCaptureFixture) -> None:
    calls: list[dict[str, Any]] = []

    async def flaky(**kwargs: Any) -> Any:
        calls.append(kwargs)
        if "response_format" in kwargs:
            raise RuntimeError("native structured output unsupported")
        return _completion('{"x": 1}')

    r = Reasoner(name="t", model="openai:gpt-4o", reply=SCHEMA)
    with caplog.at_level(logging.WARNING, "composable_agents.execution.llm"):
        result = asyncio.run(complete_reasoner(r, "hi", acompletion=flaky))

    assert result.reply == {"x": 1}
    assert len(calls) == 2
    assert result.meta.response_format_fallback is not None
    assert "native structured output unsupported" in result.meta.response_format_fallback
    assert result.meta.to_attrs()["llm.response_format_fallback"] == (
        result.meta.response_format_fallback)
    assert any("response_format" in rec.message for rec in caplog.records)


def test_no_fallback_attr_on_clean_native() -> None:
    async def ok(**kwargs: Any) -> Any:
        return _completion('{"x": 1}')

    r = Reasoner(name="t", model="openai:gpt-4o", reply=SCHEMA)
    result = asyncio.run(complete_reasoner(r, "hi", acompletion=ok))
    assert result.meta.response_format_fallback is None
    assert "llm.response_format_fallback" not in result.meta.to_attrs()
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_llm_fallback_recorded.py -v`
Expected: FAIL — `LlmCallMeta` has no `response_format_fallback`.

- [ ] **Step 3: Implement**

`llm_result.py`: add field `response_format_fallback: str | None = None` after `cost`, and in `to_attrs`:

```python
        if self.response_format_fallback is not None:
            out["llm.response_format_fallback"] = self.response_format_fallback
```

`llm.py`: add module logger (`import logging` / `logger = logging.getLogger(__name__)` near the imports). Rework the dispatch in `complete_reasoner` — a CONFIG-class error (bad key, unknown model, malformed request) must re-raise, never be masked by the fallback (same contract as the resilient caller, `resilience.py` module docstring):

```python
    started = time.time()
    fallback_reason: Optional[str] = None
    if schema is not None and provider not in _PROMPT_FALLBACK_PROVIDERS:
        try:
            completion = await call(native=True)
        except Exception as exc:
            if classify_error(exc) is ErrorClass.CONFIG:
                raise  # auth/config failure — fallback must never mask it
            # Provider/any-llm could not honor response_format; reissue with the
            # schema injected into the prompt — recorded, never silent (G-8).
            fallback_reason = repr(exc)
            logger.warning(
                "response_format fallback for %s (%s): retrying prompt-injected: %s",
                reasoner.name, provider, fallback_reason,
            )
            completion = await call(native=False)
    else:
        completion = await call(native=False)
```

(`classify_error` / `ErrorClass` are already imported at llm.py:44-51.) Thread it into the meta: `response_format_fallback=fallback_reason,`. Add to the test file a CONFIG case:

```python
def test_config_error_not_masked_by_fallback() -> None:
    class AuthError(Exception):
        status_code = 401

    async def unauthorized(**kwargs: Any) -> Any:
        if "response_format" in kwargs:
            raise AuthError("invalid api key")
        return _completion('{"x": 1}')   # fallback would "succeed" — must not run

    r = Reasoner(name="t", model="openai:gpt-4o", reply=SCHEMA)
    with pytest.raises(AuthError):
        asyncio.run(complete_reasoner(r, "hi", acompletion=unauthorized))
```

(Verify `classify_error` maps a `status_code == 401` exception to `ErrorClass.CONFIG`; if its heuristics key off something else, shape the fake accordingly — the point is a CONFIG-classified exception, not the literal attribute.)

- [ ] **Step 4: Run tests + gates**

Run: `python -m pytest tests/test_llm_fallback_recorded.py tests/test_llm.py -v && python -m pytest && uv run mypy --strict composable_agents && ruff check composable_agents` → PASS/clean (full run guards attr-snapshot tests in projection/Langfuse suites)

- [ ] **Step 5: Commit** — `git commit -am "fix(phase1): record + log response_format fallback instead of silent downgrade"`

---

### Task 6: `output_retries` — bounded re-ask on unparseable schema'd replies

**Files:**
- Modify: `composable_agents/execution/llm.py` (`complete_reasoner` reply handling)
- Modify: `composable_agents/execution/llm_result.py` (`output_retries_used: int = 0` + attr)
- Test: `tests/test_llm_output_retries.py`

**Interfaces:**
- Consumes: `Reasoner.output_retries` (Task 2).
- Produces: when `reply_schema` is set and the parsed reply is not a `dict`, the same call is reissued up to `output_retries` times; `LlmCallMeta.output_retries_used` counts reissues; `to_attrs()` emits `"llm.output_retries"` only when > 0. The resilient caller's MODEL_BEHAVIOR ladder-advance (llm.py:495-503) stays as the *next* escalation after retries are exhausted — unchanged.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_llm_output_retries.py
import asyncio
from types import SimpleNamespace
from typing import Any

from composable_agents.dotctx import Reasoner
from composable_agents.execution.llm import complete_reasoner

SCHEMA = {"type": "object", "properties": {"x": {"type": "integer"}}}


def _completion(content: str) -> Any:
    msg = SimpleNamespace(content=content, parsed=None)
    return SimpleNamespace(choices=[SimpleNamespace(message=msg)],
                           usage=None, model="m")


def _reasoner(retries: int) -> Reasoner:
    return Reasoner(name="t", model="gemini:gemini-2.5-flash",  # prompt-fallback provider: single path
                    reply=SCHEMA, output_retries=retries)


def test_reask_until_parse() -> None:
    replies = iter(["not json", "still not json", '{"x": 2}'])

    async def acompletion(**kwargs: Any) -> Any:
        return _completion(next(replies))

    result = asyncio.run(complete_reasoner(_reasoner(2), "hi", acompletion=acompletion))
    assert result.reply == {"x": 2}
    assert result.meta.output_retries_used == 2
    assert result.meta.to_attrs()["llm.output_retries"] == 2


def test_exhausted_returns_last_raw_reply() -> None:
    async def acompletion(**kwargs: Any) -> Any:
        return _completion("garbage")

    result = asyncio.run(complete_reasoner(_reasoner(1), "hi", acompletion=acompletion))
    assert result.reply == "garbage"          # resilient caller/strict interpret escalates from here
    assert result.meta.output_retries_used == 1


def test_zero_retries_is_single_call() -> None:
    calls = []

    async def acompletion(**kwargs: Any) -> Any:
        calls.append(1)
        return _completion("garbage")

    asyncio.run(complete_reasoner(_reasoner(0), "hi", acompletion=acompletion))
    assert len(calls) == 1
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_llm_output_retries.py -v`
Expected: FAIL — no `output_retries_used`; single call only.

- [ ] **Step 3: Implement**

`llm_result.py`: add `output_retries_used: int = 0` after `response_format_fallback`, and in `to_attrs`:

```python
        if self.output_retries_used:
            out["llm.output_retries"] = self.output_retries_used
```

`llm.py` — first extend the `call` closure with an optional corrective turn appended after the user message (a real re-ask, not a blind reissue):

```python
    async def call(*, native: bool, retry_note: Optional[str] = None) -> Any:
        ...  # existing body; after building `messages`, before acompletion:
        if retry_note is not None:
            messages.append({"role": "user", "content": retry_note})
```

Then wrap dispatch + parse in a bounded loop. Replace the block from `started = time.time()` through `reply = _parse_reply(...)` with:

```python
    started = time.time()
    fallback_reason: Optional[str] = None
    native_ok = True   # latched: after one response_format failure, never retry native
    retries_used = 0

    async def dispatch_once(retry_note: Optional[str] = None) -> Any:
        nonlocal fallback_reason, native_ok
        if schema is not None and native_ok and provider not in _PROMPT_FALLBACK_PROVIDERS:
            try:
                return await call(native=True, retry_note=retry_note)
            except Exception as exc:
                if classify_error(exc) is ErrorClass.CONFIG:
                    raise  # auth/config failure — fallback must never mask it
                native_ok = False
                fallback_reason = repr(exc)   # first downgrade only, by the latch
                logger.warning(
                    "response_format fallback for %s (%s): retrying prompt-injected: %s",
                    reasoner.name, provider, fallback_reason,
                )
        return await call(native=False, retry_note=retry_note)

    completion = await dispatch_once()
    reply = _parse_reply(completion, expect_json=schema is not None)
    while (
        schema is not None
        and not isinstance(reply, dict)
        and retries_used < reasoner.output_retries
    ):
        retries_used += 1
        logger.warning(
            "reply for %s did not parse as JSON object; re-ask %d/%d",
            reasoner.name, retries_used, reasoner.output_retries,
        )
        completion = await dispatch_once(
            retry_note=(
                "Your previous reply was not a single valid JSON object matching "
                "the required schema. Reply again with ONLY the JSON object."
            )
        )
        reply = _parse_reply(completion, expect_json=True)
    ended = time.time()
```

and thread `output_retries_used=retries_used,` into the meta. (This subsumes and refactors Task 5's dispatch — the CONFIG re-raise and first-downgrade recording carry over; the latch guarantees the reason is never overwritten and native is not re-attempted per retry.) Extend the first test to assert the corrective turn actually reaches the provider:

```python
def test_reask_carries_corrective_message() -> None:
    seen_messages: list[list[dict]] = []
    replies = iter(["not json", '{"x": 2}'])

    async def acompletion(**kwargs: Any) -> Any:
        seen_messages.append(kwargs["messages"])
        return _completion(next(replies))

    asyncio.run(complete_reasoner(_reasoner(1), "hi", acompletion=acompletion))
    assert len(seen_messages) == 2
    assert "not a single valid JSON object" in seen_messages[1][-1]["content"]
    assert len(seen_messages[1]) == len(seen_messages[0]) + 1
```

- [ ] **Step 4: Run tests + gates**

Run: `python -m pytest tests/test_llm_output_retries.py tests/test_llm_fallback_recorded.py tests/test_resilient_llm.py -v && python -m pytest && uv run mypy --strict composable_agents && ruff check composable_agents` → PASS/clean

- [ ] **Step 5: Commit** — `git commit -am "feat(phase1): bounded output_retries re-ask for schema'd replies"`

---

### Task 7: Yglu-evaluated settings behind a `[yglu]` extra, with explicit env

**Files:**
- Create: `composable_agents/dotctx_yglu.py`
- Modify: `pyproject.toml:35-47` (add extra `yglu = ["yglu>=1.0"]`)
- Modify: `composable_agents/dotctx.py:276-307` (`load_dotctx` env param + tag detection)
- Modify: `composable_agents/dotctx_rich.py:595-624` (`_read_settings`/`load_rich_dotctx` env threading)
- Test: `tests/test_dotctx_yglu.py`

**Interfaces:**
- Produces: `dotctx_yglu.load_settings(text: str, *, env: Mapping[str, str] | None, filepath: str) -> dict[str, Any]`; `dotctx_yglu.has_yglu_tags(text: str) -> bool`; `dotctx_yglu.set_default_env(env: Mapping[str, str] | None) -> None` / `default_env() -> Mapping[str, str] | None` (module-level binding the CLI sets in Task 8); `load_dotctx(path, *, env=None)` and `load_rich_dotctx(path, ..., env=None)`.
- Env semantics: during yglu evaluation, `os.environ` is *swapped* for exactly `{**env, "YGLU_ENABLE_ENV": "1"}` — declared vars only, no ambient leakage, deterministic freeze. `env=None` falls back to `default_env()`; if that is also None, `$env.get(var, default)` sees an empty environment and yields defaults. Not thread-safe; CLI/load-time only (documented).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_dotctx_yglu.py
import os
import pytest

yglu = pytest.importorskip("yglu")

from composable_agents.dotctx import load_dotctx
from composable_agents.dotctx_yglu import has_yglu_tags, load_settings

SETTINGS = 'model: !? $env.get("SUMMARY_MODEL", "openai/gpt-5.4-nano@medium")\n'


def test_has_yglu_tags() -> None:
    assert has_yglu_tags(SETTINGS)
    assert not has_yglu_tags("model: openai:gpt-4o\n")


def test_env_default_when_unset() -> None:
    out = load_settings(SETTINGS, env={}, filepath="settings.yaml")
    assert out["model"] == "openai/gpt-5.4-nano@medium"


def test_explicit_env_wins_and_ambient_never_leaks() -> None:
    os.environ["SUMMARY_MODEL"] = "ambient:leak"
    try:
        out = load_settings(SETTINGS, env={"SUMMARY_MODEL": "openai:gpt-5.5@low"},
                            filepath="settings.yaml")
        assert out["model"] == "openai:gpt-5.5@low"
        out2 = load_settings(SETTINGS, env={}, filepath="settings.yaml")
        assert out2["model"] == "openai/gpt-5.4-nano@medium"   # ambient invisible
    finally:
        del os.environ["SUMMARY_MODEL"]


def test_load_dotctx_end_to_end(tmp_path) -> None:
    d = tmp_path / "summary.ctx"
    d.mkdir()
    (d / "settings.yaml").write_text(SETTINGS)
    r = load_dotctx(str(d), env={"SUMMARY_MODEL": "anthropic:claude-sonnet-4-6@high"})
    assert r.model == "anthropic:claude-sonnet-4-6"
    assert r.reasoning_effort == "high"
```

Also (no yglu installed path — separate test, no importorskip):

```python
def test_tagged_settings_without_yglu_is_hard_error(tmp_path, monkeypatch) -> None:
    import composable_agents.dotctx_yglu as dy
    monkeypatch.setattr(dy, "_import_yglu", lambda: (_ for _ in ()).throw(
        ImportError("no yglu")))
    d = tmp_path / "t.ctx"
    d.mkdir()
    (d / "settings.yaml").write_text(SETTINGS)
    with pytest.raises(ImportError, match=r"composable-agents\[yglu\]"):
        load_dotctx(str(d))
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_dotctx_yglu.py -v`
Expected: FAIL — `ModuleNotFoundError: composable_agents.dotctx_yglu`

- [ ] **Step 3: Implement**

`pyproject.toml` after the `dotctx` extra:

```toml
# Yglu-evaluated settings.yaml (mem-mcp .ctx compatibility). $env reads come
# from an explicit mapping, never ambient os.environ.
yglu = ["yglu>=1.0"]
```

```python
# composable_agents/dotctx_yglu.py
"""Yglu-evaluated ``settings.yaml`` with an explicit ``$env`` binding.

mem-mcp's ``.ctx`` settings use yglu expressions — universally
``!? $env.get("VAR", default)`` — for env-dependent model/round config. To keep
freezes deterministic, ``$env`` never reads the ambient process environment
here: callers pass the mapping (the ``ca`` env profile), and ``os.environ`` is
swapped for exactly that mapping while yglu evaluates. Load/CLI-time only —
the swap is process-global and not thread-safe.

Requires the ``composable-agents[yglu]`` extra; evaluating a tagged file
without yglu is a hard, actionable error (G-8: no silent fallback).
"""
from __future__ import annotations

import io
import os
import re
from contextlib import contextmanager
from typing import Any, Iterator, Mapping, Optional

_TAG_RE = re.compile(r"!\?|!\(\)|!if\b|!for\b|!concat\b|!merge\b")
_DEFAULT_ENV: Optional[Mapping[str, str]] = None


def has_yglu_tags(text: str) -> bool:
    return _TAG_RE.search(text) is not None


def set_default_env(env: Optional[Mapping[str, str]]) -> None:
    global _DEFAULT_ENV
    _DEFAULT_ENV = None if env is None else dict(env)


def default_env() -> Optional[Mapping[str, str]]:
    return _DEFAULT_ENV


def _import_yglu() -> Any:
    try:
        from yglu import builder
    except ImportError as exc:
        raise ImportError(
            "settings.yaml uses yglu expressions; install composable-agents[yglu]"
        ) from exc
    return builder


@contextmanager
def _exact_environ(env: Mapping[str, str]) -> Iterator[None]:
    saved = dict(os.environ)
    try:
        os.environ.clear()
        os.environ.update({**env, "YGLU_ENABLE_ENV": "1"})
        yield
    finally:
        os.environ.clear()
        os.environ.update(saved)


def load_settings(
    text: str, *, env: Optional[Mapping[str, str]], filepath: str
) -> dict[str, Any]:
    builder = _import_yglu()
    binding = dict(env) if env is not None else dict(default_env() or {})
    with _exact_environ(binding):
        result = builder.build(io.StringIO(text), filepath=filepath)
        # yglu expressions evaluate lazily during dict conversion — convert
        # inside the environ swap (mirrors mem-mcp's loader).
        settings = dict(result) if result else {}
    if not isinstance(settings, dict):
        raise ValueError(f"settings must be a YAML mapping: {filepath!r}")
    return settings


__all__ = ["default_env", "has_yglu_tags", "load_settings", "set_default_env"]
```

`dotctx.py` — `load_dotctx` grows `*, env: Optional[Mapping[str, str]] = None`, threads it to the rich loader, and swaps the parse:

```python
def load_dotctx(path: str, *, env: Optional[Mapping[str, str]] = None) -> Reasoner:
    if is_rich_dotctx(path):
        from . import dotctx_rich
        return dotctx_rich.load_rich_dotctx(path, env=env).reasoner
    ...
    with open(settings_path, "r", encoding="utf-8") as fh:
        text = fh.read()
    from .dotctx_yglu import has_yglu_tags, load_settings as load_yglu_settings
    if has_yglu_tags(text):
        settings = load_yglu_settings(text, env=env, filepath=settings_path)
    else:
        try:
            import yaml
        except ModuleNotFoundError as e:  # pragma: no cover
            raise RuntimeError("PyYAML is required to load a dotctx from disk") from e
        settings = yaml.safe_load(text) or {}
```

(`dotctx_yglu` itself imports nothing optional at module scope, so this import is always safe.) `dotctx_rich.py` — `_read_settings(path, *, env=None)` gets the same tag-check-then-yglu treatment around its `yaml.safe_load`, and `load_rich_dotctx(..., env=None)` passes through.

- [ ] **Step 4: Run tests + gates**

Run: `uv pip install 'yglu>=1.0'` (dev env), then `python -m pytest tests/test_dotctx_yglu.py -v && python -m pytest && uv run mypy --strict composable_agents && ruff check composable_agents` → PASS/clean. Also verify bare-install safety: `python -c "import composable_agents"` in an env without yglu still imports.

- [ ] **Step 5: Commit** — `git commit -am "feat(phase1): [yglu] extra — yglu-evaluated settings with explicit env binding"`

---

### Task 8: `ca` env vars → dotctx default env

**Files:**
- Modify: `composable_agents/ca/config.py:14-31` (`EnvConfig.vars`) and the env-table merge (`_env_fields`/`_build_envs`, `:44-90`)
- Modify: `composable_agents/ca/resolve.py` and `composable_agents/ca/_resolve_child.py` — thread `env_vars` through the resolver child payload; `composable_agents/ca/deploy.py:114` area (freeze subprocess) likewise
- Modify: `composable_agents/ca/cli.py:114-135` (`run`) and `:165-185` (`deploy`) — pass `cfg.envs[env].vars` into the resolver/freeze invocations
- Test: `tests/ca/test_env_vars.py`

**Interfaces:**
- Consumes: `dotctx_yglu.set_default_env` (Task 7).
- Produces: `[env.<name>.vars]` (ca.toml) / `[tool.ca.env.<name>.vars]` (pyproject) → `EnvConfig.vars: dict[str, str]` — table names are SINGULAR `env`, matching the existing convention (`config.py:106`, `tests/ca/test_envconfig.py:36,82`). The binding must reach the process that imports user modules: `ca run`/`lint`/`deploy` resolve and freeze in a **subprocess** (`runner.py:19` → `resolve.py:35` → `_resolve_child.py:75`), so `set_default_env` is called inside `_resolve_child.main()` from a payload field, not in `cli.py`'s own process.

- [ ] **Step 1: Write the failing tests**

```python
# tests/ca/test_env_vars.py
from pathlib import Path

from composable_agents.ca.config import load_config


def test_env_vars_parsed(tmp_path: Path) -> None:
    (tmp_path / "ca.toml").write_text(
        '[env.prod]\n'
        'task_queue = "prod-q"\n'
        '[env.prod.vars]\n'
        'SUMMARY_MODEL = "anthropic:claude-sonnet-4-6@high"\n'
    )
    cfg = load_config(tmp_path)
    assert cfg.envs["prod"].vars == {
        "SUMMARY_MODEL": "anthropic:claude-sonnet-4-6@high"}


def test_env_vars_default_empty(tmp_path: Path) -> None:
    cfg = load_config(tmp_path)
    assert cfg.envs["local"].vars == {}
```

End-to-end child-process test (the load-bearing one — a user module that calls `load_dotctx` at import time must see the binding):

```python
def test_run_binds_env_vars_in_resolver_child(tmp_path: Path) -> None:
    ctx = tmp_path / "flows" / "summary.ctx"
    ctx.mkdir(parents=True)
    (ctx / "settings.yaml").write_text(
        'model: !? $env.get("SUMMARY_MODEL", "openai:gpt-4o")\n')
    (tmp_path / "flows" / "mod.py").write_text(
        "from composable_agents.dotctx import load_dotctx\n"
        "import os\n"
        "R = load_dotctx(os.path.join(os.path.dirname(__file__), 'summary.ctx'))\n"
    )
    (tmp_path / "ca.toml").write_text(
        'src = ["flows"]\n'
        '[env.prod.vars]\nSUMMARY_MODEL = "anthropic:claude-sonnet-4-6@high"\n'
    )
    # Drive the same resolve path `ca run --env prod` uses (see resolve.py's
    # public entry; call it with env_vars from the loaded config) and assert
    # the resolved reasoner's model is the prod binding, not the default.
```

Complete the driver against `resolve.py`'s actual public function signature when implementing — the assertion is `model == "anthropic:claude-sonnet-4-6"` with `reasoning_effort == "high"`.

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/ca/test_env_vars.py -v`
Expected: FAIL — `EnvConfig` has no `vars`; child test fails on the default model.

- [ ] **Step 3: Implement**

`config.py`: add `vars: dict[str, str] = field(default_factory=dict)` to `EnvConfig`. In the env-table merge (`_build_envs`), pop the `"vars"` sub-table from each raw env table, `str()`-coerce keys/values, and merge ca.toml over pyproject (same order as scalar fields); construct `EnvConfig(vars=...)`.

`resolve.py` / `_resolve_child.py`: add an `env_vars: dict[str, str] | None` field to the child payload (same JSON channel the resolver already uses). In `_resolve_child.main()`, BEFORE `_discover_modules`/`importlib.import_module` (line 75):

```python
    if payload_env_vars is not None:
        from composable_agents.dotctx_yglu import set_default_env
        set_default_env(payload_env_vars)
```

`deploy.py` (freeze subprocess, line 114 area): thread the same field through the freeze/freeze_check child.

`cli.py`: `run` (line 114 area) and `deploy` (line 165 area) pass `cfg.envs[env].vars` into their resolve/freeze calls. `lint` passes the `local` env's vars. No `set_default_env` call in `cli.py`'s own process is needed or wanted — the child owns the binding for its lifetime and exits.

- [ ] **Step 4: Run tests + gates**

Run: `python -m pytest tests/ca/test_env_vars.py tests/ca/test_envconfig.py -v && python -m pytest tests/ca && uv run mypy --strict composable_agents && ruff check composable_agents` → PASS/clean

- [ ] **Step 5: Commit** — `git commit -am "feat(phase1): ca env vars bind dotctx yglu env per --env"`

---

### Task 9: `ca --version` reads package metadata

**Files:**
- Modify: `composable_agents/ca/cli.py:35` and `:44-51`
- Test: `tests/test_ca_version.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_ca_version.py
from importlib.metadata import version

from typer.testing import CliRunner

from composable_agents.ca.cli import app


def test_version_matches_package() -> None:
    result = CliRunner().invoke(app, ["--version"])
    assert result.exit_code == 0
    assert version("composable-agents") in result.output
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_ca_version.py -v`
Expected: FAIL — output is `ca 0.1.0`.

- [ ] **Step 3: Implement** — replace line 35:

```python
def _package_version() -> str:
    from importlib.metadata import PackageNotFoundError, version
    try:
        return version("composable-agents")
    except PackageNotFoundError:  # editable/source checkout without metadata
        return "unknown"


VERSION = _package_version()
```

- [ ] **Step 4: Run** — `python -m pytest tests/test_ca_version.py -v && uv run mypy --strict composable_agents && ruff check composable_agents` → PASS/clean

- [ ] **Step 5: Commit** — `git commit -am "fix(phase1): ca --version from importlib.metadata"`

---

## Acceptance demo (post-plan sanity, not a task)

Copy one real mem-mcp prompt dir (e.g. `apps/memory-api/prompts/episodic/episode_summary.ctx`) into a scratch dir, run `load_dotctx(path, env={})`, and confirm: model canonicalized, effort populated, no exceptions. Differences found here (role-marker templates, `messages/` layout, `response_format:`/`require_tool_call:` keys — both *deliberately deferred*: they configure the agent loop, which is Phase 3/4 scope) go into the Phase 2 backlog, not this plan.

## Explicit non-goals (deferred by design)

- `require_tool_call`, nested `response_format:` settings keys (agent-loop concerns; rich loader will still reject them as unknown keys — the acceptance demo documents which prompts hit this).
- mem-mcp's single-file `.ctx` frontmatter + `<<< role:... >>>` markers and `eval.py`/`eval.yaml` (Phase 2 dotctx-compat scope).
- Native tool-calling, MCP client, resilience-policy port, CAS/wasm work (Phases 2–4 per the adoption roadmap).
