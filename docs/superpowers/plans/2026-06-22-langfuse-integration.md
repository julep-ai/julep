# Langfuse Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Export every `composable_agents` run to Langfuse (run/DAG traces + LLM generations with usage/cost/model + cost/latency dashboards) via OTLP-native export, with no vendor SDK in core.

**Architecture:** Capture → carry → export. The `LlmCaller` returns a typed `LlmResult{reply, meta}`; `meta` (usage, served model, wall-clock, attempts) rides the existing `Result.attrs` → `ProjectionEvent.attrs` seam (no event-schema change). A new `execution/langfuse.py` (the `langfuse` extra) folds the projection's `SpanData` into an OTel span tree with a synthetic root, deterministic primary-parent nesting, stable derived IDs, and `gen_ai.*`/`langfuse.*` attributes, then ships it over OTLP/HTTP to Langfuse. Export always runs outside the workflow.

**Tech Stack:** Python ≥3.12, OpenTelemetry SDK + OTLP/HTTP exporter, any-llm (providers), Temporal, pytest, mypy --strict.

**Design spec:** `docs/superpowers/specs/2026-06-22-langfuse-integration-design.md`

## Global Constraints

- Python floor: `requires-python = ">=3.12"`. New optional deps go in extras, never core `dependencies`.
- All new/changed code in `composable_agents` must pass `uv run mypy --strict composable_agents` (package only, not tests).
- Run tests with `python -m pytest` (not bare `pytest`).
- The projection's logical `ts` is deterministic (replay-safe) — **never** use it for span timing. Wall-clock comes from `meta`, captured on the non-deterministic (activity) side.
- `opentelemetry` and the OTLP exporter are optional: every import of them is guarded (`HAVE_OTEL`-style), and pure code paths work without them — mirror `execution/otel.py`.
- Follow the existing module docstring style (a prose paragraph explaining the seam) on every new module.
- Capturing prompt/completion bodies (`io_refs`) is **off by default** (PII/size); gate behind an explicit `capture_io` flag.

---

## File Structure

| File | Responsibility | New? |
|---|---|---|
| `composable_agents/execution/llm_result.py` | `LlmResult`/`LlmCallMeta`/`AttemptMeta` dataclasses (pure, no deps) | new |
| `composable_agents/execution/llm.py` | capture usage+model+wall-clock in `complete_reasoner`; resilience caller returns `LlmResult` | modify |
| `composable_agents/execution/effects.py` | unwrap `LlmResult` at `invokeReasoner`, put `meta` into `Result.attrs` | modify |
| `composable_agents/projection.py` | enrich `SpanData`; `to_otel_spans` carries attrs/cost/value_ref/event-ids | modify |
| `composable_agents/execution/otel.py` | set `attrs` on spans; use wall-clock start/end from attrs | modify |
| `composable_agents/execution/langfuse.py` | IdGenerator, span tree, attribute mapping, `configure_langfuse`, `export_run_to_langfuse` | new |
| `composable_agents/execution/openai_batch.py` | capture per-`custom_id` usage in `parse` | modify |
| `composable_agents/execution/anthropic_batch.py` | capture per-`custom_id` usage in `parse` | modify |
| `composable_agents/execution/reasoner_batch.py` | route batch usage into the `attrs` path | modify |
| `composable_agents/agent.py` | opt-in local/facade Langfuse export after a run | modify |
| `pyproject.toml` | `langfuse` extra | modify |
| `tests/execution/test_*` | unit tests per task | new |
| `spikes/langfuse_otlp/` | de-risk spike script (manual) | new |

---

## Task 0: De-risk spike — OTLP → real Langfuse (manual, do first)

**Files:**
- Create: `spikes/langfuse_otlp/spike.py`

**Why:** Retire the one real unknown — exact Langfuse OTLP attribute keys and tree/cost rendering — before building against assumptions. This task is exploratory (not TDD); its deliverable is *confirmed facts* recorded back into the spec's appendix.

- [ ] **Step 1: Write a minimal OTLP emitter**

```python
# spikes/langfuse_otlp/spike.py
"""Push one synthetic run to a real Langfuse via OTLP to pin attribute keys.

Env: LANGFUSE_HOST, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY.
Run: python spikes/langfuse_otlp/spike.py
"""
import base64, os, time
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

host = os.environ["LANGFUSE_HOST"].rstrip("/")
auth = base64.b64encode(
    f'{os.environ["LANGFUSE_PUBLIC_KEY"]}:{os.environ["LANGFUSE_SECRET_KEY"]}'.encode()
).decode()
exporter = OTLPSpanExporter(
    endpoint=f"{host}/api/public/otel/v1/traces",
    headers={"Authorization": f"Basic {auth}", "x-langfuse-ingestion-version": "4"},
)
provider = TracerProvider()
provider.add_span_processor(BatchSpanProcessor(exporter))
trace.set_tracer_provider(provider)
tr = trace.get_tracer("spike")

now = time.time_ns()
with tr.start_as_current_span("run-root", start_time=now) as root:
    root.set_attribute("langfuse.trace.name", "spike-run")
    root.set_attribute("langfuse.session.id", "spike-session")
    with tr.start_as_current_span("reasoner-call", start_time=now) as gen:
        gen.set_attribute("langfuse.observation.type", "generation")
        gen.set_attribute("gen_ai.request.model", "claude-opus-4-8")
        gen.set_attribute("gen_ai.usage.input_tokens", 1200)
        gen.set_attribute("gen_ai.usage.output_tokens", 340)
        gen.set_attribute("langfuse.observation.input", '{"q": "hi"}')
        gen.set_attribute("langfuse.observation.output", '{"a": "hello"}')
        gen.end(end_time=now + 2_000_000_000)
    root.end(end_time=now + 2_500_000_000)
provider.shutdown()
print("flushed")
```

- [ ] **Step 2: Run against a Langfuse instance and verify in the UI**

Run: `python spikes/langfuse_otlp/spike.py`
Verify in Langfuse: (a) one trace named `spike-run`; (b) `reasoner-call` nested under `run-root`; (c) the generation shows input/output tokens and a derived **cost**; (d) latency ≈ 2s. Re-run once and confirm whether IDs collide (SDK-random IDs will create a *second* trace — that motivates Task 6's stable IDs).

- [ ] **Step 3: Record findings into the spec appendix**

Append a short "Spike results (2026-06-22)" subsection to `docs/superpowers/specs/2026-06-22-langfuse-integration-design.md` listing the exact attribute keys that worked, the endpoint path, and whether cost rendered from `gen_ai.usage.*`. If any key differs from this plan, update the affected tasks before implementing them. Commit:

```bash
git add spikes/langfuse_otlp/spike.py docs/superpowers/specs/2026-06-22-langfuse-integration-design.md
git commit -m "spike: confirm Langfuse OTLP attribute keys"
```

---

## Task 1: `LlmResult` / `LlmCallMeta` types + capture in `complete_reasoner`

**Files:**
- Create: `composable_agents/execution/llm_result.py`
- Modify: `composable_agents/execution/llm.py` (`complete_reasoner`, ~220-267)
- Test: `tests/execution/test_llm_result.py`

**Interfaces:**
- Produces:
  - `AttemptMeta(model: str, provider: str, outcome: str, input_tokens: int | None, output_tokens: int | None, ms: float | None)`
  - `LlmCallMeta(served_model: str, provider: str, input_tokens: int | None, output_tokens: int | None, total_tokens: int | None, started_at: float | None, ended_at: float | None, attempts: tuple[AttemptMeta, ...], cost: float | None)` with `.to_attrs() -> dict[str, Any]`
  - `LlmResult(reply: Any, meta: LlmCallMeta)`
  - `complete_reasoner(...) -> LlmResult` (was `-> Any`)

- [ ] **Step 1: Write the failing test**

```python
# tests/execution/test_llm_result.py
import asyncio
from types import SimpleNamespace
from composable_agents.execution.llm_result import LlmResult, LlmCallMeta
from composable_agents.execution import llm as llm_mod
from composable_agents.dotctx import Reasoner

def _fake_completion(content="hello", pt=11, ct=7):
    msg = SimpleNamespace(content=content, parsed=None)
    choice = SimpleNamespace(message=msg)
    usage = SimpleNamespace(prompt_tokens=pt, completion_tokens=ct, total_tokens=pt + ct)
    return SimpleNamespace(choices=[choice], usage=usage, model="anthropic/claude-x")

def test_complete_reasoner_returns_result_with_usage():
    async def fake_acompletion(**kwargs):
        return _fake_completion()
    reasoner = Reasoner(name="r", model="anthropic:claude-x", system="s", reply_schema=None)
    out = asyncio.run(llm_mod.complete_reasoner(
        reasoner, {"x": 1}, acompletion=fake_acompletion,
    ))
    assert isinstance(out, LlmResult)
    assert out.reply == "hello"
    assert out.meta.input_tokens == 11
    assert out.meta.output_tokens == 7
    assert out.meta.total_tokens == 18
    assert out.meta.started_at is not None and out.meta.ended_at is not None
    assert out.meta.ended_at >= out.meta.started_at
    assert out.meta.served_model == "claude-x"

def test_to_attrs_shape():
    meta = LlmCallMeta(
        served_model="m", provider="p", input_tokens=1, output_tokens=2,
        total_tokens=3, started_at=10.0, ended_at=12.0, attempts=(), cost=None,
    )
    attrs = meta.to_attrs()
    assert attrs["llm.model"] == "m"
    assert attrs["llm.usage"] == {"input": 1, "output": 2, "total": 3}
    assert attrs["llm.started_at"] == 10.0
    assert attrs["llm.ended_at"] == 12.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/execution/test_llm_result.py -v`
Expected: FAIL — `llm_result` module missing / `complete_reasoner` returns a bare reply.

- [ ] **Step 3: Implement `llm_result.py`**

```python
# composable_agents/execution/llm_result.py
"""Typed result envelope for a single reasoner model call.

The ``LlmCaller`` seam returns the parsed reply *and* the metadata an
observability sink needs (served model, token usage, wall-clock window, and the
per-attempt ladder the resilience caller walked). ``meta.to_attrs()`` renders a
vendor-neutral dict that rides the existing ``Result.attrs`` ->
``ProjectionEvent.attrs`` seam; the Langfuse exporter maps it to gen_ai/langfuse
attributes downstream. Pure module: no IO, no engine imports.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class AttemptMeta:
    model: str
    provider: str
    outcome: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    ms: float | None = None

@dataclass(frozen=True)
class LlmCallMeta:
    served_model: str
    provider: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    started_at: float | None = None
    ended_at: float | None = None
    attempts: tuple[AttemptMeta, ...] = ()
    cost: float | None = None

    def to_attrs(self) -> dict[str, Any]:
        out: dict[str, Any] = {"llm.model": self.served_model, "llm.provider": self.provider}
        if self.input_tokens is not None or self.output_tokens is not None:
            out["llm.usage"] = {
                "input": self.input_tokens,
                "output": self.output_tokens,
                "total": self.total_tokens,
            }
        if self.started_at is not None:
            out["llm.started_at"] = self.started_at
        if self.ended_at is not None:
            out["llm.ended_at"] = self.ended_at
        if self.cost is not None:
            out["llm.cost"] = self.cost
        if self.attempts:
            out["llm.attempts"] = [
                {"model": a.model, "provider": a.provider, "outcome": a.outcome,
                 "input": a.input_tokens, "output": a.output_tokens, "ms": a.ms}
                for a in self.attempts
            ]
        return out

@dataclass(frozen=True)
class LlmResult:
    reply: Any
    meta: LlmCallMeta
```

- [ ] **Step 4: Capture usage + wall-clock in `complete_reasoner`**

In `llm.py`, add `import time` and a helper, then change the tail of `complete_reasoner` (the `return _parse_reply(...)` at ~267) to capture timing + usage and return an `LlmResult`. Use a `_usage_of(completion)` helper tolerant of missing `.usage`:

```python
# add near the other helpers in llm.py
import time
from .llm_result import AttemptMeta, LlmCallMeta, LlmResult  # noqa: E402 (top of file)

def _usage_of(completion: Any) -> tuple[int | None, int | None, int | None]:
    usage = getattr(completion, "usage", None)
    if usage is None:
        return None, None, None
    pt = getattr(usage, "prompt_tokens", None)
    ct = getattr(usage, "completion_tokens", None)
    tt = getattr(usage, "total_tokens", None)
    if tt is None and pt is not None and ct is not None:
        tt = pt + ct
    return pt, ct, tt

def _served_model_of(completion: Any, fallback: str) -> str:
    m = getattr(completion, "model", None)
    if not isinstance(m, str) or not m:
        return fallback
    return m.split("/", 1)[1] if "/" in m else m
```

Then, replacing the `return _parse_reply(...)` line:

```python
    started = time.time()
    # ... existing native/fallback completion selection stays unchanged ...
    ended = time.time()
    reply = _parse_reply(completion, expect_json=schema is not None)
    pt, ct, tt = _usage_of(completion)
    meta = LlmCallMeta(
        served_model=_served_model_of(completion, model),
        provider=provider,
        input_tokens=pt, output_tokens=ct, total_tokens=tt,
        started_at=started, ended_at=ended,
    )
    return LlmResult(reply=reply, meta=meta)
```

(Move `started = time.time()` to just before the `if schema is not None ...` completion-selection block, and `ended = time.time()` to just after it.)

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/execution/test_llm_result.py -v`
Expected: PASS (2 tests).

- [ ] **Step 6: Typecheck + commit**

Run: `uv run mypy --strict composable_agents`
Expected: no new errors. (Downstream callers in Tasks 2–3 still expect a bare reply — those are fixed there; if mypy flags the return type now, that's expected and resolved by Task 2.)

```bash
git add composable_agents/execution/llm_result.py composable_agents/execution/llm.py tests/execution/test_llm_result.py
git commit -m "feat(llm): capture usage + wall-clock into LlmResult envelope"
```

---

## Task 2: Resilience caller returns `LlmResult` (with attempts ladder)

**Files:**
- Modify: `composable_agents/execution/llm.py` (the resilience `caller`, ~395-468)
- Test: `tests/execution/test_resilience_meta.py`

**Interfaces:**
- Consumes: `complete_reasoner(...) -> LlmResult` (Task 1); `AttemptMeta`, `LlmCallMeta`, `LlmResult`.
- Produces: the resilience `caller(...)` now returns `LlmResult` whose `meta.attempts` lists every provider attempt (including failed/skipped/fallback) and whose top-level usage/served_model come from the successful attempt.

- [ ] **Step 1: Write the failing test**

```python
# tests/execution/test_resilience_meta.py
import asyncio
from types import SimpleNamespace
from composable_agents.execution.llm import make_resilient_llm_caller  # see Step 3 name note
from composable_agents.execution.llm_result import LlmResult
from composable_agents.resilience import ResiliencePolicy
from composable_agents.dotctx import Reasoner

def _completion(pt=5, ct=3):
    msg = SimpleNamespace(content="ok", parsed=None)
    usage = SimpleNamespace(prompt_tokens=pt, completion_tokens=ct, total_tokens=pt + ct)
    return SimpleNamespace(choices=[SimpleNamespace(message=msg)], usage=usage, model="anthropic/m2")

def test_caller_returns_result_and_records_fallback_attempts():
    calls = {"n": 0}
    async def flaky(**kwargs):
        calls["n"] += 1
        if kwargs["model"] == "m1":
            raise TimeoutError("provider down")
        return _completion()
    policy = ResiliencePolicy(fallbacks={"m1": ["m2"]})  # m1 -> m2; adapt to real ctor
    caller = make_resilient_llm_caller(policy=policy, acompletion=flaky)
    reasoner = Reasoner(name="r", model="anthropic:m1", system="s", reply_schema=None)
    out = asyncio.run(caller(reasoner, {"x": 1}))
    assert isinstance(out, LlmResult)
    assert out.reply == "ok"
    assert out.meta.served_model == "m2"
    assert out.meta.input_tokens == 5
    outcomes = [a.outcome for a in out.meta.attempts]
    assert outcomes[-1] == "ok"
    assert any(o != "ok" for o in outcomes)  # the m1 failure is recorded
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/execution/test_resilience_meta.py -v`
Expected: FAIL — caller returns a bare reply / no `meta`.

- [ ] **Step 3: Thread `LlmResult` through the resilience loop**

In `llm.py`'s resilience `caller` (the factory currently producing `caller`, around line 395; note its real public name from the `__all__` list and reuse it — the test's `make_resilient_llm_caller` is a placeholder, replace with the actual factory name), change the success path to keep the `LlmResult` and stamp the attempts ladder. The loop already builds an `attempts: list[AttemptRecord]`. Convert those to `AttemptMeta` and attach to the winning result's meta:

```python
    # in the success branch, where it currently does:
    #     record = AttemptRecord(model=model, provider=provider, outcome="ok")
    #     attempts.append(record); _notify(record); return reply
    # change `reply = await complete_reasoner(...)` so it keeps the LlmResult:
    result = await complete_reasoner(
        candidate, value, acompletion=resolved,
        default_provider=default_provider, transcript=transcript, dispatch=dispatch,
    )
    reply = result.reply
    # ... existing breaker.record_success + schema-dict check use `reply` ...
    ok_record = AttemptRecord(model=model, provider=provider, outcome="ok")
    attempts.append(ok_record); _notify(ok_record)
    meta = dataclasses.replace(
        result.meta,
        attempts=tuple(
            AttemptMeta(model=a.model, provider=a.provider, outcome=a.outcome)
            for a in attempts
        ),
    )
    return LlmResult(reply=reply, meta=meta)
```

Add `import dataclasses` if not present, and `from .llm_result import AttemptMeta, LlmResult`. The `except`/schema-misbehavior branches keep using `complete_reasoner`'s reply via `result.reply`; update the `except` to call `complete_reasoner` and read `.reply` consistently. The non-resilient `make_llm_caller`/`make_local_reasoner` seams (Task 1 changed `complete_reasoner`) must also return `LlmResult` or unwrap — make those callers return `LlmResult` too for a uniform seam.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/execution/test_resilience_meta.py tests/execution/test_llm_result.py -v`
Expected: PASS.

- [ ] **Step 5: Run the existing llm test suite (guard against regressions)**

Run: `python -m pytest tests/ -k "llm or caller or reasoner" -v`
Expected: PASS. Any test asserting `caller(...)` returns a bare reply must be updated to read `.reply` — do that in this commit.

- [ ] **Step 6: Typecheck + commit**

Run: `uv run mypy --strict composable_agents`

```bash
git add composable_agents/execution/llm.py tests/execution/test_resilience_meta.py
git commit -m "feat(llm): resilience caller returns LlmResult with attempt ladder"
```

---

## Task 3: Unwrap `LlmResult` at `invokeReasoner`, carry `meta` into `Result.attrs`

**Files:**
- Modify: `composable_agents/execution/effects.py` (the `invokeReasoner` effect that calls `_CTX.llm(...)`)
- Test: `tests/execution/test_reasoner_attrs.py`

**Interfaces:**
- Consumes: `_CTX.llm(...) -> LlmResult | Any` (Task 2); `interpreter.py` already emits `did(..., attrs=out.attrs)` from the reasoner `Result.attrs`.
- Produces: the reasoner activation's `Did` projection event carries `attrs` including `llm.model`, `llm.usage`, `llm.started_at`, `llm.ended_at`, `llm.attempts`.

- [ ] **Step 1: Write the failing test**

```python
# tests/execution/test_reasoner_attrs.py
import asyncio
from composable_agents.execution.effects import _unwrap_llm  # helper added in Step 3
from composable_agents.execution.llm_result import LlmResult, LlmCallMeta

def test_unwrap_llm_result():
    meta = LlmCallMeta(served_model="m", provider="p", input_tokens=1,
                       output_tokens=2, total_tokens=3, started_at=1.0, ended_at=2.0)
    reply, attrs = _unwrap_llm(LlmResult(reply={"a": 1}, meta=meta))
    assert reply == {"a": 1}
    assert attrs["llm.model"] == "m"
    assert attrs["llm.usage"] == {"input": 1, "output": 2, "total": 3}

def test_unwrap_bare_reply_backcompat():
    reply, attrs = _unwrap_llm({"a": 1})  # a fake caller that returns a bare reply
    assert reply == {"a": 1}
    assert attrs == {}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/execution/test_reasoner_attrs.py -v`
Expected: FAIL — `_unwrap_llm` does not exist.

- [ ] **Step 3: Add `_unwrap_llm` and use it where the effect calls the caller**

```python
# effects.py — near the other private helpers
from .llm_result import LlmResult

def _unwrap_llm(out: Any) -> tuple[Any, dict[str, Any]]:
    """Accept either an LlmResult or a bare reply (back-compat for fake callers)."""
    if isinstance(out, LlmResult):
        return out.reply, out.meta.to_attrs()
    return out, {}
```

Find the `invokeReasoner` effect body where it `await`s `_CTX.llm(reasoner, value, ...)` and returns a `Result`. Change it to unwrap and merge attrs:

```python
    raw = await _CTX.llm(reasoner, value, principal, transcript, dispatch)
    reply, llm_attrs = _unwrap_llm(raw)
    # ... existing reply interpretation (interpret_reasoner_reply / compilePlan) uses `reply` ...
    return Result(value=<existing value>, attrs={**(<existing attrs> or {}), **llm_attrs})
```

If the effect currently returns `Result(value=...)` with no attrs, pass `attrs=llm_attrs`. Keep every other field identical.

- [ ] **Step 4: Add an end-to-end projection assertion**

```python
# append to tests/execution/test_reasoner_attrs.py
from composable_agents.agent import Agent  # or the lowest-cost facade that runs a reasoner

def test_did_event_carries_llm_usage():
    # Build a minimal agent/flow with one reasoner, inject a fake llm returning LlmResult,
    # run it, then inspect the in-memory projection events for a DID whose attrs carry llm.usage.
    # Use the same fake-llm injection pattern the existing agent tests use (Agent(..., llm=fake)).
    ...
    # assert any(e.type.name == "DID" and "llm.usage" in e.attrs for e in emitter.store.events())
```

Fill this in using the existing `Agent(..., llm=...)` fake-injection pattern from `tests/` (grep `llm=` in tests for the canonical shape). It must assert a `DID` event's `attrs` contains `llm.usage`.

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/execution/test_reasoner_attrs.py -v`
Expected: PASS.

- [ ] **Step 6: Typecheck + commit**

Run: `uv run mypy --strict composable_agents`

```bash
git add composable_agents/execution/effects.py tests/execution/test_reasoner_attrs.py
git commit -m "feat(effects): carry LLM usage meta into reasoner Did attrs"
```

---

## Task 4: Enrich `SpanData` + `to_otel_spans`

**Files:**
- Modify: `composable_agents/projection.py` (`SpanData` ~316; `to_otel_spans` ~328)
- Test: `tests/test_projection_spandata.py`

**Interfaces:**
- Produces: `SpanData` gains `attrs: dict[str, Any] = field(default_factory=dict)`, `cost: float | None = None`, `value_ref: str | None = None`, `planned_event_id: str | None = None`, `terminal_event_id: str | None = None`. `to_otel_spans` populates them from the planned + terminal events.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_projection_spandata.py
from composable_agents.projection import ProjectionEvent, EventType, to_otel_spans

def _ev(**kw):
    base = dict(event_id="e0", type=EventType.PLANNED, node="n", cid="c0", ts=0.0)
    base.update(kw); return ProjectionEvent(**base)

def test_spandata_carries_attrs_cost_refs():
    planned = _ev(event_id="e0", type=EventType.PLANNED, node="n", cid="c0", ts=0.0)
    did = _ev(event_id="e1", type=EventType.DID, node="n", cid="c0", ts=1.0,
              causes=("e0",), value_ref="val:abc", cost=0.02,
              attrs={"llm.model": "m", "llm.usage": {"input": 1, "output": 2, "total": 3}})
    spans = to_otel_spans([planned, did])
    s = spans[0]
    assert s.cost == 0.02
    assert s.value_ref == "val:abc"
    assert s.attrs["llm.model"] == "m"
    assert s.planned_event_id == "e0"
    assert s.terminal_event_id == "e1"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_projection_spandata.py -v`
Expected: FAIL — `SpanData` has no `attrs`/`cost`/`value_ref`/event-id fields.

- [ ] **Step 3: Extend `SpanData` and `to_otel_spans`**

```python
# projection.py — SpanData
@dataclass(frozen=True)
class SpanData:
    name: str
    cid: str
    node: str
    start_ts: float
    end_ts: Optional[float]
    status: str
    parents: tuple[str, ...]
    error: Optional[str] = None
    attrs: dict[str, Any] = field(default_factory=dict)
    cost: Optional[float] = None
    value_ref: Optional[str] = None
    planned_event_id: Optional[str] = None
    terminal_event_id: Optional[str] = None
```

In `to_otel_spans`, when building each span, copy from the planned + terminal events. For the terminal (`end`) branch:

```python
            spans.append(SpanData(
                name=start.node, cid=cid, node=start.node,
                start_ts=start.ts, end_ts=end.ts, status=status,
                parents=parents, error=end.error,
                attrs={**start.attrs, **end.attrs},
                cost=end.cost, value_ref=end.value_ref,
                planned_event_id=start.event_id, terminal_event_id=end.event_id,
            ))
```

For the unfinished branch, set `attrs=dict(start.attrs)`, `planned_event_id=start.event_id`, leave `cost`/`value_ref`/`terminal_event_id` as defaults.

- [ ] **Step 4: Run tests + the existing projection suite**

Run: `python -m pytest tests/test_projection_spandata.py tests/ -k projection -v`
Expected: PASS (existing `spans_to_dicts` tests unaffected — new fields default empty).

- [ ] **Step 5: Typecheck + commit**

Run: `uv run mypy --strict composable_agents`

```bash
git add composable_agents/projection.py tests/test_projection_spandata.py
git commit -m "feat(projection): SpanData carries attrs/cost/value_ref/event-ids"
```

---

## Task 5: `otel.py` — set attrs on spans + wall-clock start/end

**Files:**
- Modify: `composable_agents/execution/otel.py` (`export_spans` ~63-107; `spans_to_dicts` ~36-56)
- Test: `tests/execution/test_otel_attrs.py`

**Interfaces:**
- Consumes: enriched `SpanData` (Task 4).
- Produces: `export_spans` sets every `SpanData.attrs` key as a span attribute and uses `attrs["llm.started_at"]`/`attrs["llm.ended_at"]` (seconds) for span start/end when present; `spans_to_dicts` includes `attrs`/`cost`.

- [ ] **Step 1: Write the failing test**

```python
# tests/execution/test_otel_attrs.py
from composable_agents.projection import SpanData
from composable_agents.execution import otel

class _FakeSpan:
    def __init__(self): self.attrs = {}; self.start = None; self.end = None
    def set_attribute(self, k, v): self.attrs[k] = v
    def set_status(self, *_a, **_k): pass
    def record_exception(self, *_a, **_k): pass
    def get_span_context(self): return object()
    def end(self, end_time=None): self.end = end_time

class _FakeTracer:
    def __init__(self): self.spans = []; self.starts = []
    def start_span(self, name, start_time=None, links=None):
        self.starts.append(start_time); s = _FakeSpan(); self.spans.append(s); return s

def test_export_sets_attrs_and_wallclock():
    tr = _FakeTracer()
    span = SpanData(
        name="reasoner", cid="c0", node="reasoner", start_ts=0.0, end_ts=1.0,
        status="ok", parents=(),
        attrs={"llm.model": "m", "llm.started_at": 100.0, "llm.ended_at": 102.0},
        cost=0.01,
    )
    otel.export_spans([_planned_for(span)] + [], tracer=tr)  # see note
```

Note: `export_spans` takes *events*, not `SpanData`. Write the test to build a planned+did event pair (as in Task 4) whose DID `attrs` carry `llm.started_at`/`llm.ended_at`, pass them to `export_spans(events, tracer=tr)`, then assert `tr.starts[0] == int(100.0 * 1e9)` and `tr.spans[0].attrs["llm.model"] == "m"`. Use the `_ev` helper from Task 4.

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/execution/test_otel_attrs.py -v`
Expected: FAIL — attrs not set; start time uses logical `ts`.

- [ ] **Step 3: Implement**

In `export_spans`, after creating each span, set attrs and prefer wall-clock:

```python
    for s in spans:
        links = [Link(contexts[p]) for p in s.parents if p in contexts]
        start_ns = _ns(s.attrs.get("llm.started_at", s.start_ts))
        span = tr.start_span(s.name, start_time=start_ns, links=links)
        span.set_attribute("ca.cid", s.cid)
        span.set_attribute("ca.node", s.node)
        for k, v in s.attrs.items():
            span.set_attribute(k, v if isinstance(v, (str, int, float, bool)) else _json(v))
        if s.cost is not None:
            span.set_attribute("ca.cost", s.cost)
        # ... existing status handling ...
        contexts[s.cid] = span.get_span_context()
        end_src = s.attrs.get("llm.ended_at", s.end_ts)
        if end_src is not None:
            span.end(end_time=_ns(end_src))
        count += 1
```

Add a small `_json(v)` helper (`json.dumps(v, default=str)`) for non-scalar attrs. Also add `attrs`/`cost` to each dict in `spans_to_dicts`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/execution/test_otel_attrs.py tests/ -k otel -v`
Expected: PASS.

- [ ] **Step 5: Typecheck + commit**

Run: `uv run mypy --strict composable_agents`

```bash
git add composable_agents/execution/otel.py tests/execution/test_otel_attrs.py
git commit -m "feat(otel): set span attrs + wall-clock start/end from projection attrs"
```

---

## Task 6: `langfuse.py` — stable `IdGenerator`

**Files:**
- Create: `composable_agents/execution/langfuse.py`
- Test: `tests/execution/test_langfuse_ids.py`

**Interfaces:**
- Produces:
  - `trace_id_for(run_id: str) -> int` (128-bit), `span_id_for(cid: str) -> int` (64-bit)
  - `StableIdGenerator(run_id: str)` implementing OTel's `IdGenerator` (`generate_trace_id`, `generate_span_id`) — deterministic per `(run_id, cid)`; uses a contextvar/threadlocal to know the current `cid` (set by the exporter before starting each span).

- [ ] **Step 1: Write the failing test**

```python
# tests/execution/test_langfuse_ids.py
from composable_agents.execution.langfuse import trace_id_for, span_id_for

def test_ids_are_stable_and_sized():
    assert trace_id_for("run-1") == trace_id_for("run-1")
    assert trace_id_for("run-1") != trace_id_for("run-2")
    assert 0 < trace_id_for("run-1") < (1 << 128)
    assert 0 < span_id_for("c0") < (1 << 64)
    assert span_id_for("c0") != span_id_for("c1")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/execution/test_langfuse_ids.py -v`
Expected: FAIL — module/functions missing.

- [ ] **Step 3: Implement the ID helpers (guarded OTel import)**

```python
# composable_agents/execution/langfuse.py  (top)
"""Langfuse export of a run's projection (OTLP/HTTP, GenAI semantic conventions).

The generic OTel exporter (execution/otel.py) emits a link-based DAG for any
backend. Langfuse renders a strict tree and ignores OTel links, so this module
owns the Langfuse-specific shaping: one synthetic root span per run, a
deterministic primary-parent tree, stable IDs derived from run_id/cid (so
history re-export is idempotent), and gen_ai/langfuse attribute mapping. The
OpenTelemetry SDK + OTLP exporter are optional; imports are guarded.
"""
from __future__ import annotations
import hashlib
from typing import Any, Sequence
from ..projection import ProjectionEvent, SpanData, to_otel_spans

def trace_id_for(run_id: str) -> int:
    h = hashlib.sha256(("trace:" + run_id).encode()).digest()
    return int.from_bytes(h[:16], "big") or 1

def span_id_for(cid: str) -> int:
    h = hashlib.sha256(("span:" + cid).encode()).digest()
    return int.from_bytes(h[:8], "big") or 1
```

The `StableIdGenerator` class (subclassing `opentelemetry.sdk.trace.id_generator.IdGenerator`) goes behind the guarded import added in Task 9; for this task only the pure functions are needed.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/execution/test_langfuse_ids.py -v`
Expected: PASS.

- [ ] **Step 5: Typecheck + commit**

Run: `uv run mypy --strict composable_agents`

```bash
git add composable_agents/execution/langfuse.py tests/execution/test_langfuse_ids.py
git commit -m "feat(langfuse): stable trace/span IDs from run_id/cid"
```

---

## Task 7: `langfuse.py` — DAG→tree builder (synthetic root, primary parent, links)

**Files:**
- Modify: `composable_agents/execution/langfuse.py`
- Test: `tests/execution/test_langfuse_tree.py`

**Interfaces:**
- Produces: `build_tree(spans: Sequence[SpanData], run_id: str) -> list[TreeNode]` where `TreeNode(span: SpanData | None, span_id: int, parent_id: int | None, link_ids: tuple[int, ...], is_root: bool)`. Exactly one root (`is_root=True`, synthetic, `span=None`). Each non-root node's `parent_id` = `span_id_for(primary cause cid)` or the root. Non-primary causes become `link_ids`. Deterministic topological order; cycles/orphans fall back to the root.

- [ ] **Step 1: Write the failing test**

```python
# tests/execution/test_langfuse_tree.py
from composable_agents.projection import SpanData
from composable_agents.execution.langfuse import build_tree, span_id_for

def _s(cid, parents=()):
    return SpanData(name=cid, cid=cid, node=cid, start_ts=0.0, end_ts=1.0,
                    status="ok", parents=tuple(parents))

def test_single_root_and_primary_parent():
    spans = [_s("a"), _s("b", ["a"]), _s("c", ["a", "b"])]
    nodes = build_tree(spans, run_id="r")
    roots = [n for n in nodes if n.is_root]
    assert len(roots) == 1
    by_cid = {n.span.cid: n for n in nodes if n.span is not None}
    assert by_cid["a"].parent_id == roots[0].span_id        # no cause -> root
    assert by_cid["b"].parent_id == span_id_for("a")        # primary = first cause
    assert by_cid["c"].parent_id == span_id_for("a")        # first cause
    assert span_id_for("b") in by_cid["c"].link_ids         # extra cause -> link

def test_cycle_falls_back_to_root():
    spans = [_s("x", ["y"]), _s("y", ["x"])]
    nodes = build_tree(spans, run_id="r")
    # neither x nor y may list the other as an ancestor chain that loops; both resolve
    assert all(n.parent_id is not None for n in nodes if not n.is_root)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/execution/test_langfuse_tree.py -v`
Expected: FAIL — `build_tree`/`TreeNode` missing.

- [ ] **Step 3: Implement `TreeNode` + `build_tree`**

```python
# langfuse.py
from dataclasses import dataclass

@dataclass(frozen=True)
class TreeNode:
    span: SpanData | None
    span_id: int
    parent_id: int | None
    link_ids: tuple[int, ...]
    is_root: bool

_ROOT_CID = "__run_root__"

def build_tree(spans: Sequence[SpanData], run_id: str) -> list[TreeNode]:
    root_id = span_id_for(_ROOT_CID + ":" + run_id)
    present = {s.cid for s in spans}
    # deterministic order: by start_ts then cid
    ordered = sorted(spans, key=lambda s: (s.start_ts, s.cid))
    nodes: list[TreeNode] = [TreeNode(span=None, span_id=root_id, parent_id=None,
                                      link_ids=(), is_root=True)]
    def resolves_without_cycle(cid: str, primary: str) -> bool:
        # walk primary-parent chain; if we return to cid, it's a cycle
        seen = {cid}; cur = primary; chain = {s.cid: (s.parents[0] if s.parents else None)
                                              for s in spans}
        while cur is not None and cur in present:
            if cur in seen: return False
            seen.add(cur); cur = chain.get(cur)
        return True
    for s in ordered:
        causes = [c for c in s.parents if c in present]
        primary = causes[0] if causes else None
        if primary is not None and not resolves_without_cycle(s.cid, primary):
            primary = None  # cycle -> attach to root
        parent_id = span_id_for(primary) if primary is not None else root_id
        links = tuple(span_id_for(c) for c in causes[1:]) if causes else ()
        nodes.append(TreeNode(span=s, span_id=span_id_for(s.cid),
                              parent_id=parent_id, link_ids=links, is_root=False))
    return nodes
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/execution/test_langfuse_tree.py -v`
Expected: PASS.

- [ ] **Step 5: Typecheck + commit**

Run: `uv run mypy --strict composable_agents`

```bash
git add composable_agents/execution/langfuse.py tests/execution/test_langfuse_tree.py
git commit -m "feat(langfuse): DAG->tree builder with synthetic root + primary parent"
```

---

## Task 8: `langfuse.py` — attribute mapping (gen_ai.* + langfuse.*)

**Files:**
- Modify: `composable_agents/execution/langfuse.py`
- Test: `tests/execution/test_langfuse_attrs.py`

**Interfaces:**
- Produces: `span_attributes(span: SpanData, *, session_id: str, trace_name: str, capture_io: bool) -> dict[str, Any]` mapping `SpanData.attrs` to Langfuse/GenAI keys and tagging generations.

- [ ] **Step 1: Write the failing test**

```python
# tests/execution/test_langfuse_attrs.py
from composable_agents.projection import SpanData
from composable_agents.execution.langfuse import span_attributes

def _gen_span():
    return SpanData(
        name="reasoner", cid="c0", node="reasoner", start_ts=0.0, end_ts=1.0,
        status="ok", parents=(),
        attrs={"llm.model": "claude-opus-4-8",
               "llm.usage": {"input": 1200, "output": 340, "total": 1540}},
    )

def test_generation_mapping():
    a = span_attributes(_gen_span(), session_id="s1", trace_name="run", capture_io=False)
    assert a["langfuse.observation.type"] == "generation"
    assert a["gen_ai.request.model"] == "claude-opus-4-8"
    assert a["gen_ai.usage.input_tokens"] == 1200
    assert a["gen_ai.usage.output_tokens"] == 340
    assert a["langfuse.session.id"] == "s1"
    assert a["langfuse.trace.name"] == "run"

def test_plain_span_is_not_generation():
    s = SpanData(name="pure", cid="c1", node="pure", start_ts=0.0, end_ts=1.0,
                 status="ok", parents=(), attrs={})
    a = span_attributes(s, session_id="s1", trace_name="run", capture_io=False)
    assert a.get("langfuse.observation.type") != "generation"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/execution/test_langfuse_attrs.py -v`
Expected: FAIL — `span_attributes` missing.

- [ ] **Step 3: Implement**

```python
# langfuse.py
def span_attributes(span: SpanData, *, session_id: str, trace_name: str,
                    capture_io: bool) -> dict[str, Any]:
    out: dict[str, Any] = {
        "langfuse.session.id": session_id,
        "langfuse.trace.name": trace_name,
        "ca.cid": span.cid,
        "ca.node": span.node,
    }
    usage = span.attrs.get("llm.usage")
    model = span.attrs.get("llm.model")
    is_generation = model is not None or usage is not None
    if is_generation:
        out["langfuse.observation.type"] = "generation"
        if model is not None:
            out["gen_ai.request.model"] = model
            out["gen_ai.response.model"] = model
        if isinstance(usage, dict):
            if usage.get("input") is not None:
                out["gen_ai.usage.input_tokens"] = usage["input"]
            if usage.get("output") is not None:
                out["gen_ai.usage.output_tokens"] = usage["output"]
    if span.cost is not None:
        out["gen_ai.usage.cost"] = span.cost
    if capture_io:
        if "llm.input" in span.attrs:
            out["langfuse.observation.input"] = span.attrs["llm.input"]
        if "llm.output" in span.attrs:
            out["langfuse.observation.output"] = span.attrs["llm.output"]
    if span.attrs.get("llm.attempts"):
        out["ca.llm.attempts"] = _json(span.attrs["llm.attempts"])
    return out
```

Reuse the `_json` helper (move it to `langfuse.py` or import from `otel.py`). Confirm the exact `gen_ai.usage.cost` / cost key against the Task 0 spike results and adjust if Langfuse expects a different key.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/execution/test_langfuse_attrs.py -v`
Expected: PASS.

- [ ] **Step 5: Typecheck + commit**

Run: `uv run mypy --strict composable_agents`

```bash
git add composable_agents/execution/langfuse.py tests/execution/test_langfuse_attrs.py
git commit -m "feat(langfuse): gen_ai/langfuse attribute mapping + generation tagging"
```

---

## Task 9: `langfuse.py` — `configure_langfuse()` (OTLP exporter, auth, flush)

**Files:**
- Modify: `composable_agents/execution/langfuse.py`
- Test: `tests/execution/test_langfuse_config.py`

**Interfaces:**
- Produces:
  - `LangfuseConfig(host: str, public_key: str, secret_key: str, capture_io: bool = False)` with `.from_env() -> LangfuseConfig`, `.endpoint() -> str`, `.headers() -> dict[str, str]`.
  - `configure_langfuse(config: LangfuseConfig | None = None) -> LangfuseExporterHandle` building a `TracerProvider` + `BatchSpanProcessor` + `OTLPSpanExporter`; handle exposes `.tracer`, `.flush()`, `.shutdown()`.

- [ ] **Step 1: Write the failing test (config building only — no network)**

```python
# tests/execution/test_langfuse_config.py
import base64
from composable_agents.execution.langfuse import LangfuseConfig

def test_endpoint_and_headers():
    cfg = LangfuseConfig(host="https://lf.example.com/", public_key="pk", secret_key="sk")
    assert cfg.endpoint() == "https://lf.example.com/api/public/otel/v1/traces"
    h = cfg.headers()
    assert h["x-langfuse-ingestion-version"] == "4"
    assert h["Authorization"] == "Basic " + base64.b64encode(b"pk:sk").decode()

def test_from_env(monkeypatch):
    monkeypatch.setenv("LANGFUSE_HOST", "https://h")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "p")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "s")
    cfg = LangfuseConfig.from_env()
    assert cfg.host == "https://h" and cfg.public_key == "p" and cfg.secret_key == "s"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/execution/test_langfuse_config.py -v`
Expected: FAIL — `LangfuseConfig` missing.

- [ ] **Step 3: Implement config + guarded exporter wiring**

```python
# langfuse.py
import base64, os
from dataclasses import dataclass

try:
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    HAVE_OTLP = True
except ModuleNotFoundError:
    HAVE_OTLP = False

@dataclass(frozen=True)
class LangfuseConfig:
    host: str
    public_key: str
    secret_key: str
    capture_io: bool = False

    @staticmethod
    def from_env() -> "LangfuseConfig":
        return LangfuseConfig(
            host=os.environ["LANGFUSE_HOST"],
            public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
            secret_key=os.environ["LANGFUSE_SECRET_KEY"],
            capture_io=os.environ.get("LANGFUSE_CAPTURE_IO", "").lower() in ("1", "true"),
        )

    def endpoint(self) -> str:
        return self.host.rstrip("/") + "/api/public/otel/v1/traces"

    def headers(self) -> dict[str, str]:
        auth = base64.b64encode(f"{self.public_key}:{self.secret_key}".encode()).decode()
        return {"Authorization": f"Basic {auth}", "x-langfuse-ingestion-version": "4"}

@dataclass
class LangfuseExporterHandle:
    tracer: Any
    _provider: Any
    def flush(self) -> None: self._provider.force_flush()
    def shutdown(self) -> None: self._provider.shutdown()

def configure_langfuse(config: "LangfuseConfig | None" = None) -> "LangfuseExporterHandle":
    if not HAVE_OTLP:
        raise RuntimeError("configure_langfuse requires composable-agents[langfuse]")
    cfg = config or LangfuseConfig.from_env()
    exporter = OTLPSpanExporter(endpoint=cfg.endpoint(), headers=cfg.headers())
    provider = TracerProvider()
    provider.add_span_processor(BatchSpanProcessor(exporter))
    return LangfuseExporterHandle(tracer=provider.get_tracer("composable_agents"),
                                  _provider=provider)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/execution/test_langfuse_config.py -v`
Expected: PASS.

- [ ] **Step 5: Typecheck + commit**

Run: `uv run mypy --strict composable_agents`

```bash
git add composable_agents/execution/langfuse.py tests/execution/test_langfuse_config.py
git commit -m "feat(langfuse): configure_langfuse OTLP exporter + auth + flush"
```

---

## Task 10: `langfuse.py` — `export_run_to_langfuse()` end-to-end + `langfuse` extra

**Files:**
- Modify: `composable_agents/execution/langfuse.py`, `pyproject.toml`
- Test: `tests/execution/test_langfuse_export.py`

**Interfaces:**
- Consumes: `to_otel_spans` (Task 4), `build_tree` (Task 7), `span_attributes` (Task 8), `LangfuseExporterHandle` (Task 9), stable IDs (Task 6).
- Produces: `export_run_to_langfuse(events: Sequence[ProjectionEvent], *, run_id: str, trace_name: str | None = None, session_id: str | None = None, tracer: Any, capture_io: bool = False) -> int` — emits the synthetic root + one span per `SpanData` with derived IDs, primary-parent nesting, links, mapped attributes; returns spans emitted. The synthetic root carries `langfuse.trace.name`/`langfuse.session.id`.

- [ ] **Step 1: Write the failing test (in-memory tracer, no network)**

```python
# tests/execution/test_langfuse_export.py
from composable_agents.execution.langfuse import export_run_to_langfuse, span_id_for
from composable_agents.projection import ProjectionEvent, EventType

def _planned(node, cid, eid, causes=()):
    return ProjectionEvent(event_id=eid, type=EventType.PLANNED, node=node, cid=cid, ts=0.0, causes=causes)
def _did(node, cid, eid, causes=(), attrs=None, cost=None):
    return ProjectionEvent(event_id=eid, type=EventType.DID, node=node, cid=cid, ts=1.0,
                           causes=causes, attrs=attrs or {}, cost=cost)

class _Span:
    def __init__(self, name, ctx): self.name=name; self.ctx=ctx; self.attrs={}; self.ended=False
    def set_attribute(self,k,v): self.attrs[k]=v
    def set_status(self,*a,**k): pass
    def record_exception(self,*a,**k): pass
    def get_span_context(self): return self.ctx
    def end(self, end_time=None): self.ended=True

class _Tracer:
    def __init__(self): self.spans=[]
    def start_span(self, name, start_time=None, links=None, context=None):
        s=_Span(name, object()); s.parent_ctx=context; s.links=links; self.spans.append(s); return s

def test_export_emits_root_plus_spans():
    events = [
        _planned("reasoner", "c0", "e0"),
        _did("reasoner", "c0", "e1", causes=("e0",),
             attrs={"llm.model": "m", "llm.usage": {"input": 5, "output": 2, "total": 7}}),
    ]
    tr = _Tracer()
    n = export_run_to_langfuse(events, run_id="run-1", tracer=tr, trace_name="t", session_id="s")
    assert n >= 1
    names = [s.name for s in tr.spans]
    assert any("reasoner" in nm for nm in names)
    gen = [s for s in tr.spans if s.attrs.get("langfuse.observation.type") == "generation"]
    assert gen and gen[0].attrs["gen_ai.usage.input_tokens"] == 5
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/execution/test_langfuse_export.py -v`
Expected: FAIL — `export_run_to_langfuse` missing.

- [ ] **Step 3: Implement the orchestrator**

```python
# langfuse.py
def export_run_to_langfuse(events, *, run_id, tracer, trace_name=None,
                           session_id=None, capture_io=False) -> int:
    spans = to_otel_spans(list(events))
    nodes = build_tree(spans, run_id=run_id)
    trace_name = trace_name or run_id
    session_id = session_id or run_id
    # Build OTel parent contexts keyed by span_id as we go (topo order from build_tree).
    # The synthetic root uses trace_id_for(run_id); use a non-recording parent context
    # via opentelemetry.trace.set_span_in_context. See otel.py for the link pattern.
    count = 0
    contexts: dict[int, Any] = {}
    for node in nodes:
        if node.is_root:
            root = tracer.start_span(trace_name, context=None)
            root.set_attribute("langfuse.trace.name", trace_name)
            root.set_attribute("langfuse.session.id", session_id)
            contexts[node.span_id] = _ctx_of(root)
            _root_span = root
            count += 1
            continue
        s = node.span
        parent_ctx = contexts.get(node.parent_id)
        start_ns = _ns(s.attrs.get("llm.started_at", s.start_ts))
        span = tracer.start_span(s.name, start_time=start_ns, context=parent_ctx,
                                 links=_links_for(node.link_ids, contexts))
        for k, v in span_attributes(s, session_id=session_id, trace_name=trace_name,
                                    capture_io=capture_io).items():
            span.set_attribute(k, v)
        contexts[node.span_id] = _ctx_of(span)
        end_src = s.attrs.get("llm.ended_at", s.end_ts)
        if end_src is not None:
            span.end(end_time=_ns(end_src))
        count += 1
    _root_span.end()
    return count
```

Add helpers `_ns` (seconds→ns, copy from otel.py), `_ctx_of(span)` (returns `set_span_in_context(span)`), `_links_for(ids, contexts)` (build `Link` for present ids). These need the guarded OTel `trace` import (`from opentelemetry import trace as _t`; `set_span_in_context`, `Link`). Provide a pure fallback so the in-memory-tracer test (which passes a fake tracer and never touches real OTel context) works — i.e. `_ctx_of`/`_links_for` tolerate the fake by returning lightweight placeholders when `HAVE_OTEL` is False or the span is a fake. Keep the **stable IDs** wired by installing `StableIdGenerator` on the provider in `configure_langfuse` (Task 9), OR by passing explicit ids — confirm against the spike which path the OTLP SDK honors; if the SDK ignores per-span ids, install the `IdGenerator` on the `TracerProvider` and set the current cid via a contextvar before each `start_span`.

- [ ] **Step 4: Add the `langfuse` extra to `pyproject.toml`**

```toml
# under [project.optional-dependencies]
langfuse = [
    "opentelemetry-api>=1.20",
    "opentelemetry-sdk>=1.20",
    "opentelemetry-exporter-otlp-proto-http>=1.20",
]
```

Add `opentelemetry-exporter-otlp-proto-http>=1.20` to the `dev` extra too (so the export tests can run with the real SDK in CI).

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/execution/test_langfuse_export.py -v`
Expected: PASS.

- [ ] **Step 6: Typecheck + commit**

Run: `uv run mypy --strict composable_agents`

```bash
git add composable_agents/execution/langfuse.py pyproject.toml tests/execution/test_langfuse_export.py
git commit -m "feat(langfuse): export_run_to_langfuse end-to-end + langfuse extra"
```

---

## Task 11: Local/facade opt-in export (`agent.py`)

**Files:**
- Modify: `composable_agents/agent.py` (the run path that holds the `ProjectionEmitter`, ~727/812)
- Test: `tests/test_agent_langfuse.py`

**Interfaces:**
- Consumes: `export_run_to_langfuse` (Task 10); the run's in-memory projection events + a run id.
- Produces: `Agent` accepts an optional `langfuse_export` hook (a callable `(events, run_id) -> None`, default `None`). When set, after a run completes it calls the hook with `emitter.store.events()` and the run id, then the hook flushes. A convenience `langfuse_export_hook(handle, capture_io=False)` builds the standard hook from a `LangfuseExporterHandle`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_agent_langfuse.py
def test_agent_calls_langfuse_export_hook():
    captured = {}
    def hook(events, run_id):
        captured["events"] = list(events); captured["run_id"] = run_id
    # Build the same minimal one-reasoner Agent used in tests/test_reasoner_attrs.py,
    # pass langfuse_export=hook, run it, assert the hook saw DID events + a run_id.
    ...
    assert captured["run_id"]
    assert any(e.type.name == "DID" for e in captured["events"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_agent_langfuse.py -v`
Expected: FAIL — `Agent` has no `langfuse_export` parameter.

- [ ] **Step 3: Implement the hook call**

Thread a `langfuse_export: Optional[Callable[[Sequence[ProjectionEvent], str], None]] = None` parameter through `Agent.__init__` and into the run methods at ~727/812. After the run finishes (where `emitter` is in scope and the run id is known — reuse the existing run/correlation id; if none, derive one from the root cid), call:

```python
        if self._langfuse_export is not None:
            self._langfuse_export(emitter.store.events(), run_id)
```

Add the `langfuse_export_hook(handle, *, capture_io=False)` factory in `langfuse.py`:

```python
def langfuse_export_hook(handle: "LangfuseExporterHandle", *, capture_io: bool = False):
    def _hook(events, run_id: str) -> None:
        export_run_to_langfuse(events, run_id=run_id, tracer=handle.tracer,
                               capture_io=capture_io)
        handle.flush()
    return _hook
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_agent_langfuse.py -v`
Expected: PASS.

- [ ] **Step 5: Typecheck + commit**

Run: `uv run mypy --strict composable_agents`

```bash
git add composable_agents/agent.py composable_agents/execution/langfuse.py tests/test_agent_langfuse.py
git commit -m "feat(agent): opt-in Langfuse export hook after local runs"
```

---

## Task 12: Temporal post-run exporter

**Files:**
- Modify: `composable_agents/execution/langfuse.py` (add `export_temporal_run`)
- Test: `tests/execution/test_langfuse_temporal.py`

**Interfaces:**
- Consumes: `export_run_to_langfuse`; the existing `projection` query that returns `ProjectionEvent`s for a workflow (see `harness.py` ~865 / cli.py projection usage for the exact query name + JSON shape).
- Produces: `async export_temporal_run(handle, *, client, workflow_id: str, run_id: str | None = None, trace_name=None, session_id=None, capture_io=False) -> int` — queries the workflow's projection **outside** the workflow, deserializes events via `ProjectionEvent.from_json`, calls `export_run_to_langfuse`, flushes. Uses `workflow_id` as the default `run_id`/`session_id`.

- [ ] **Step 1: Write the failing test (fake client/handle — no Temporal server)**

```python
# tests/execution/test_langfuse_temporal.py
import asyncio
from composable_agents.execution.langfuse import export_temporal_run
from composable_agents.projection import ProjectionEvent, EventType

class _FakeHandleObj:
    def __init__(self, events_json): self._e = events_json
    async def query(self, name): return self._e

class _FakeClient:
    def __init__(self, events_json): self._e = events_json
    def get_workflow_handle(self, wid): return _FakeHandleObj(self._e)

class _ExpHandle:
    def __init__(self): self.tracer = _Tracer(); self.flushed = False
    def flush(self): self.flushed = True

def test_export_temporal_run_queries_and_exports():
    events_json = [
        ProjectionEvent("e0", EventType.PLANNED, "reasoner", "c0", 0.0).to_json(),
        ProjectionEvent("e1", EventType.DID, "reasoner", "c0", 1.0, causes=("e0",),
                        attrs={"llm.model": "m", "llm.usage": {"input": 1, "output": 1, "total": 2}}).to_json(),
    ]
    handle = _ExpHandle()
    n = asyncio.run(export_temporal_run(handle, client=_FakeClient(events_json),
                                        workflow_id="wf-1"))
    assert n >= 1 and handle.flushed
```

(Reuse the `_Tracer` fake from `test_langfuse_export.py` — import or duplicate it.)

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/execution/test_langfuse_temporal.py -v`
Expected: FAIL — `export_temporal_run` missing.

- [ ] **Step 3: Implement (confirm the real query name)**

```python
# langfuse.py
async def export_temporal_run(handle, *, client, workflow_id, run_id=None,
                              trace_name=None, session_id=None, capture_io=False) -> int:
    wf = client.get_workflow_handle(workflow_id)
    raw = await wf.query("projection")  # confirm exact query name in harness.py
    events = [ProjectionEvent.from_json(d) for d in raw]
    rid = run_id or workflow_id
    n = export_run_to_langfuse(events, run_id=rid, tracer=handle.tracer,
                               trace_name=trace_name or workflow_id,
                               session_id=session_id or workflow_id, capture_io=capture_io)
    handle.flush()
    return n
```

Verify the query name and return shape against `harness.py`/`cli.py` (grep `query(` and `"projection"`). If the query returns already-deserialized events, drop the `from_json` map. Document in the module docstring that this runs **outside** the workflow (determinism-safe) and that history-tail is the durable path for completed/expired workflows (follow-up).

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/execution/test_langfuse_temporal.py -v`
Expected: PASS.

- [ ] **Step 5: Typecheck + commit**

Run: `uv run mypy --strict composable_agents`

```bash
git add composable_agents/execution/langfuse.py tests/execution/test_langfuse_temporal.py
git commit -m "feat(langfuse): Temporal post-run exporter via projection query"
```

---

## Task 13: Capture batch usage in the batch adapters

**Files:**
- Modify: `composable_agents/execution/openai_batch.py` (`parse`, ~134), `composable_agents/execution/anthropic_batch.py` (`parse`, ~125)
- Test: `tests/execution/test_batch_usage.py`

**Interfaces:**
- Produces: each batch adapter's reply-parsing path surfaces per-`custom_id` usage. Define a shared `BatchReply(reply: Any, input_tokens: int | None, output_tokens: int | None)` (in `batch_provider.py` or `llm_result.py`) and have `parse` return it (or attach usage to the parsed value) so `reasoner_batch.py` (Task 14) can route it.

- [ ] **Step 1: Write the failing test**

```python
# tests/execution/test_batch_usage.py
from types import SimpleNamespace
from composable_agents.execution.openai_batch import OpenAIBatchProvider  # adapt to real class name

def test_openai_batch_parse_surfaces_usage():
    body = {
        "choices": [{"message": {"content": "ok"}}],
        "usage": {"prompt_tokens": 9, "completion_tokens": 4, "total_tokens": 13},
    }
    prov = OpenAIBatchProvider.__new__(OpenAIBatchProvider)  # avoid real client init
    out = prov.parse_with_usage(body, reasoner=SimpleNamespace(reply_schema=None))  # see Step 3
    assert out.input_tokens == 9
    assert out.output_tokens == 4
```

Write the analogous Anthropic test using a fake message object with `.usage.input_tokens`/`.usage.output_tokens` and `.content=[SimpleNamespace(type="text", text="ok")]`.

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/execution/test_batch_usage.py -v`
Expected: FAIL — no usage-bearing parse path.

- [ ] **Step 3: Implement `parse_with_usage`**

Add a `parse_with_usage(self, raw, reasoner) -> BatchReply` to each adapter that reuses the existing `parse` for the reply, plus extracts usage:
- OpenAI: `usage = raw.get("usage") or {}`; `input=usage.get("prompt_tokens")`, `output=usage.get("completion_tokens")`. (`raw` is the `response.body` dict yielded by `results`.)
- Anthropic: `u = getattr(raw, "usage", None)`; `input=getattr(u, "input_tokens", None)`, `output=getattr(u, "output_tokens", None)`. (`raw` is `result.result.message`.)

Define `BatchReply` once:

```python
# batch_provider.py (or llm_result.py)
@dataclass(frozen=True)
class BatchReply:
    reply: Any
    input_tokens: int | None = None
    output_tokens: int | None = None
```

Keep the existing `parse` intact for back-compat; `parse_with_usage` wraps it.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/execution/test_batch_usage.py -v`
Expected: PASS.

- [ ] **Step 5: Typecheck + commit**

Run: `uv run mypy --strict composable_agents`

```bash
git add composable_agents/execution/openai_batch.py composable_agents/execution/anthropic_batch.py composable_agents/execution/batch_provider.py tests/execution/test_batch_usage.py
git commit -m "feat(batch): surface per-custom_id usage from batch adapters"
```

---

## Task 14: Route batch usage into the projection `attrs` path

**Files:**
- Modify: `composable_agents/execution/reasoner_batch.py` (the result-handling path that records the batch `AttemptRecord` / produces the activation reply, ~500-560)
- Test: `tests/execution/test_batch_attrs.py`

**Interfaces:**
- Consumes: `BatchReply` (Task 13); `LlmCallMeta.to_attrs()` (Task 1).
- Produces: a batched reasoner activation's `Did` event carries the same `llm.model`/`llm.usage` attrs as a sync generation (with batch wall-clock = submit→complete window when available), so batched runs render as generations in Langfuse.

- [ ] **Step 1: Write the failing test**

```python
# tests/execution/test_batch_attrs.py
from composable_agents.execution.reasoner_batch import batch_reply_attrs  # helper added in Step 3
from composable_agents.execution.batch_provider import BatchReply

def test_batch_reply_attrs_carry_usage():
    attrs = batch_reply_attrs(
        BatchReply(reply={"a": 1}, input_tokens=20, output_tokens=8),
        model="claude-x", provider="anthropic",
        submitted_at=100.0, completed_at=160.0,
    )
    assert attrs["llm.model"] == "claude-x"
    assert attrs["llm.usage"] == {"input": 20, "output": 8, "total": 28}
    assert attrs["llm.started_at"] == 100.0
    assert attrs["llm.ended_at"] == 160.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/execution/test_batch_attrs.py -v`
Expected: FAIL — `batch_reply_attrs` missing.

- [ ] **Step 3: Implement and wire**

```python
# reasoner_batch.py
from .llm_result import LlmCallMeta

def batch_reply_attrs(br, *, model, provider, submitted_at=None, completed_at=None) -> dict:
    total = None
    if br.input_tokens is not None and br.output_tokens is not None:
        total = br.input_tokens + br.output_tokens
    meta = LlmCallMeta(
        served_model=model, provider=provider,
        input_tokens=br.input_tokens, output_tokens=br.output_tokens, total_tokens=total,
        started_at=submitted_at, ended_at=completed_at,
    )
    return meta.to_attrs()
```

Wire `parse_with_usage` into the batch result path (where it currently calls `parse` and records a coarse `AttemptRecord` at ~513): build the `attrs` via `batch_reply_attrs` and ensure they reach the activation's `Result.attrs`/`did(attrs=...)`. If the batch path emits its `Did` through a different code route than `interpreter.py`, attach the attrs at that emission point. Pull `submitted_at`/`completed_at` from the existing batch poll bookkeeping if available; otherwise leave them `None` (usage/cost still flow; only batch latency is absent — acceptable).

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/execution/test_batch_attrs.py -v`
Expected: PASS.

- [ ] **Step 5: Full suite + typecheck**

Run: `python -m pytest` then `uv run mypy --strict composable_agents`
Expected: PASS / no new errors.

- [ ] **Step 6: Commit**

```bash
git add composable_agents/execution/reasoner_batch.py tests/execution/test_batch_attrs.py
git commit -m "feat(batch): route batch usage into projection attrs (Langfuse generations)"
```

---

## Final verification

- [ ] **Full test suite:** `python -m pytest`
- [ ] **Strict typecheck:** `uv run mypy --strict composable_agents`
- [ ] **Lint:** `ruff check composable_agents tests`
- [ ] **Manual end-to-end (optional, needs a Langfuse instance):** run an example with `langfuse_export_hook` wired and confirm the trace + generation render in the Langfuse UI with tokens, cost, and latency.

## Spec coverage map

| Spec §  | Task(s) |
|---|---|
| §4.1 Capture (LlmResult) | 1, 2, 3 |
| §4.2 Carry (SpanData) | 4 |
| §4.3 Export (otel ext + langfuse) | 5, 6, 7, 8, 9, 10 |
| §4.4 Backend wiring (local + Temporal) | 11, 12 |
| §4.5 Batch coverage | 13, 14 |
| §5 Spike + testing | 0, plus per-task tests |
| §6 Risks (IDs, flush, wall-clock, batch latency) | 6, 9, 5, 14 |
