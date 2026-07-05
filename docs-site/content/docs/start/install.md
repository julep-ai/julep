---
title: "Install"
description: "Install Julep and its optional extras for durable execution, HTTP tools, OTel, multi-provider LLMs, DBOS, and CMA."
---

## Base install

```bash
pip install --pre julep
```

The base install covers flow authoring, `@flow` compilation, local `Agent.run(...)`, freeze, validation, capability checks, and the in-memory interpreter. No Temporal or other runtime dependency is required.

## Extras

### Durable execution on Temporal

```bash
pip install --pre 'julep[temporal]'
```

Adds `temporalio` and enables the durable execution layer: `FlowWorkflow`, `AgentWorkflow`, `SessionWorkflow`, client helpers (`run_flow`, `start_flow`), and worker helpers (`build_worker`, `run_worker`).

### Temporal + HTTP tools + OpenTelemetry

```bash
pip install --pre 'julep[temporal,http,otel]'
```

Adds everything in `[temporal]`, plus:

- `[http]` — `httpx` for native HTTP tool calls from the `callTool` activity.
- `[otel]` — OpenTelemetry API/SDK for exporting projection spans.

### Multi-provider LLMs

```bash
pip install --pre 'julep[providers]' 'any-llm-sdk[anthropic,openai]'
```

Adds `any-llm-sdk` and exposes `make_local_reasoner` from `julep.execution.llm`. It routes a `provider:model` prefix on `reasoner=` (e.g. `"openai:gpt-4o"`, `"gemini:gemini-2.5-flash"`) through [any-llm](https://github.com/mozilla-ai/any-llm). Requires Python ≥ 3.11.

### DBOS durable flows

```bash
pip install --pre 'julep[dbos]'
```

Adds `dbos-transact` for durable flows and agent loops on Postgres. Requires Python ≥ 3.11. See [Deploy on DBOS](/docs/deploy/dbos).

### Claude Managed Agents (CMA) backend

```bash
pip install --pre 'julep[cma]'
```

Adds `httpx` and the experimental CMA `SessionHandle` backend, which routes each turn through an Anthropic managed-agent session. Use `agent.open(backend="cma")`.

### Developer CLI

The `julep` developer CLI ships with the base install — no extra required. See [Using the CLI](/docs/guides/using-the-cli).

## Confirm the install

```python
import julep

print(julep.HAVE_TEMPORAL)
```

`HAVE_TEMPORAL` is `True` only when the guarded Temporal runtime imports successfully. The package imports and compiles flows either way.

To run the full test suite (including Temporal E2E coverage when available):

```bash
pip install -e '.[dev]'
pytest
```

<!-- ported-by ca-docs-site: start/install -->
