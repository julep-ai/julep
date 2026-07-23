---
title: "Providers & Resilience"
description: "How to configure multi-provider LLM routing, fallback chains, and circuit breakers at the LlmCaller seam."
---

## Installing provider support

The base `julep` install does not include a live LLM client. To use
real models, install the `providers` extra and any provider SDK you need:

```bash
pip install --pre 'julep[providers]' 'any-llm-sdk[anthropic,openai]'
```

Other supported extras: `[temporal]`, `[temporal,http,otel]`. See
[First Agent](/docs/start/first-agent) for the full install matrix.

## Provider:model addressing

`Reasoner.model` (and `Agent(reasoner=...)`) accepts a `provider:model` prefix
that routes the call through [any-llm](https://github.com/mozilla-ai/any-llm):

```
"openai:gpt-4o"
"anthropic:claude-sonnet-4-6"
"gemini:gemini-2.5-flash"
"groq:llama-3.3-70b"
```

A bare model string (no `provider:` prefix) falls back to the default provider
(anthropic).

## make_local_reasoner

`make_local_reasoner` from `julep.execution.llm` returns a
batteries-included async `llm=` callable. Pass it directly to `Agent(...)`:

```python
# pip install --pre 'julep[providers]' 'any-llm-sdk[anthropic,openai]'
from julep import Agent, tool
from julep.execution.llm import make_local_reasoner

agent = Agent(reasoner="openai:gpt-4o", tools=[search_kb], llm=make_local_reasoner())
```

The same agent runs on any supported provider by changing the `provider:model`
string. See
[`examples/multi_provider_agent.py`](https://github.com/julep-ai/julep-v2/blob/main/examples/multi_provider_agent.py)
for a runnable, key-guarded loop across several providers.

---

## Resilience layer

LLM providers go down. The framework's answer is a worker-side resilience layer
at the `LlmCaller` seam: a **deterministic fallback chain** per model, an
**error taxonomy** that decides retry vs. advance vs. fail-fast, and a
per-provider **circuit breaker**. Policy lives in the pure core
(`julep.resilience`); the mechanism is `make_resilient_llm_caller`
in `julep.execution.llm`.

### Wiring

```python
from julep import CircuitBreaker, ResiliencePolicy
from julep.execution.llm import make_resilient_llm_caller

policy = ResiliencePolicy(
    fallbacks={
        "openai:gpt-5.4": ("anthropic:claude-sonnet-4-6", "groq:llama-3.3-70b"),
        "anthropic:claude-opus-4-8": ("openai:gpt-5.4",),
    },
    transient_attempts=2,        # same-model attempts on 5xx/429 before advancing
    timeout_attempts=1,
)
breaker = CircuitBreaker(failure_threshold=5, cooldown_s=30.0)

llm = make_resilient_llm_caller(
    policy=policy,
    breaker=breaker,
    on_attempt=my_sink,          # AttemptRecord -> projection / OTel / logs
)

# Temporal: run_worker(..., llm=llm); DBOS: configure(WorkerContext(llm=llm)).
```

Chains use the same `"provider:model"` addressing as `Reasoner.model`. A model
without a chain entry simply has no fallbacks.

### The decision table

Every failure is classified (`classify_error`) and the next step is a pure
function of the class — same error, same decision, no randomness:

| Class | Trigger | Decision |
|---|---|---|
| `TRANSIENT` | 408/409/425/429/5xx/520/529, connection-ish messages, anything unrecognized | retry same model up to `transient_attempts` (capped backoff), then next model |
| `TIMEOUT` | `TimeoutError`, "timed out" messages | retry up to `timeout_attempts`, then next model |
| `CONFIG` | 400/401/403/404/422, bad-key / unknown-model messages | **re-raise immediately** — a fallback must never mask misconfiguration |
| `MODEL_BEHAVIOR` | `reply_schema` set but the reply is not a JSON object | next model; the breaker is **not** charged (the provider answered) |

When the whole chain fails, `ResilienceExhausted` carries the full
`AttemptRecord` log (model, provider, outcome, detail per attempt) and chains
the last provider exception as `__cause__`.

### The circuit breaker

Per-provider, process-local worker state: `failure_threshold` consecutive
failures open the circuit; after `cooldown_s` one half-open probe is allowed
through (failure re-arms the cooldown, success closes). An open circuit makes
the walk *skip* that provider's models — recorded as `skipped_open_circuit`,
never silent. Breaker state is intentionally nondeterministic across runs; it
lives in activities/steps, which are allowed to be — never read it from
workflow code.

### Engine retries: don't stack ladders

The resilient caller should be the **only** retry layer for model calls:

- **Temporal** retries `invokeReasoner`/`compilePlan` blindly
  (`ExecutionPolicy.reasoner_max_attempts`, default 4 — the historical behavior).
  When the worker's `LlmCaller` owns resilience, set `reasoner_max_attempts=1` so
  a `ResilienceExhausted` fails the activity instead of re-running the whole
  ladder three more times.
- **DBOS** reasoner steps never retry by design, so the caller is already the
  whole story there.

### Determinism, precisely

The *policy* is deterministic: candidate order, per-class attempt budgets, and
backoff are fixed by configuration. The *outcome* is not replay-deterministic —
which provider was up is a fact about the world, recorded per attempt via
`on_attempt` / `ResilienceExhausted.attempts`, never re-derived on replay.
Feed `on_attempt` into your projection sink so a run that quietly fell back
from `pro` to `medium` is visible in the trace.

<!-- ported-by julep-docs-site: guides/providers-and-resilience -->
