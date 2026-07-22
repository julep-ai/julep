---
title: "Deploy on Temporal"
description: "Durable execution on Temporal: workflows, activities, workers, guarded imports, and deployment artifacts."
---

The durable path runs the same admitted artifact as the local interpreter: a
frozen `flow_json`, a frozen `manifest_json`, pinned pure source hashes, reasoner
identity, capability manifest, framework version, and an `artifact_hash`. Only
the injected `Env` changes. Local tests use in-memory callables; Temporal uses
workflows, activities, child workflows, durable signals, and activity retry
policy. See [the project overview](/docs) and
[SPEC §6](/docs/internals/specification#6-freeze--replay-integrity).

## Prereqs

Run a Temporal dev server:

```bash
temporal server start-dev
```

Install the Temporal extra:

```bash
pip install --pre 'julep[temporal]'
```

From a source checkout, use the editable equivalent if you are running examples
against local code:

```bash
pip install -e '.[temporal]'
```

## Two deploy entry points

Raw flows deploy through `deploy(...)`:

```python
from temporalio.client import Client
from julep import deploy

deployment = deploy(flow, snapshot, capabilities=caps)
client = await Client.connect("localhost:7233")
result = await deployment.run(client, session_id="run-1", input={"q": "status"})
```

Facade agents deploy through `agent.deploy(...)`:

```python
result = await agent.deploy(client, session_id="ticket-123", input="acct-42")
```

Both paths compile the same frozen IR + manifest. `Deployment.run(...)` starts
`FlowWorkflow` through the client helper in `execution.harness`; `Agent.deploy`
delegates to `agent.deployment().run(...)` for tool-only agents. Agents with
sub-capabilities expose child artifacts through `agent.sub_deployments()`; the
worker must register those on `WorkerContext.subflows`, then run the parent via
`agent.deployment().run(...)`.

## Self-contained schema-v2 releases

`ApplicationRelease` uses `schemaVersion: 2`. Each pipeline entry carries a
`runtimeDeclarationsRef` with a content hash and byte size. The referenced,
hash-verified artifact store blob contains the reasoners and renderers needed by that
pipeline: inline reasoners retain their prompt strings; rich dotctx reasoners
retain the `.ctx` package content and portable renderer declarations. The
release manifest's tool-map shape is unchanged.

Reasoner activities fetch declarations by blob hash and cache each verified
hash in the worker process. A generic worker therefore runs released pipelines
without importing an application object. `WORKER_APPLICATION` and
`WORKER_RUNTIME_DECLARATIONS_HASH` are optional. When supplied, they must be
supplied together and are only loud cross-checks against the released
declarations; a mismatch fails the worker.

Release parsing rejects every schema version other than 2:

```text
unsupported application release schema version <v>; version 2 is required; re-publish with this julep version
```

A schema-v1 release cannot be upgraded in place. Re-publish it with this Julep
version so the declarations blob is written to artifact store.

## Standing up a worker

The worker host is the process that connects environment-specific capability to
the deterministic workflows. Use `build_worker(...)` when you own the
`temporalio.client.Client`; use `run_worker(...)` for a standalone process.

```python
from temporalio.client import Client
from julep.execution.activities import WorkerContext
from julep.execution.worker import DEFAULT_TASK_QUEUE, build_worker

client = await Client.connect("localhost:7233")
context = WorkerContext(
    tool_urls={"send_email": "https://tools.example/send_email"},
    mcp_call=my_async_mcp_caller,
    llm=my_async_llm,
    capabilities=caps,
    subflows={},
    agents={},
)
worker = build_worker(client, context, task_queue=DEFAULT_TASK_QUEUE)
await worker.run()
```

`WorkerContext` fields are process-global activity configuration: `tool_urls`
maps native tool names to HTTP URLs; `mcp_call` is async
`(server, tool, value, idempotency_key) -> result`; `llm` is async
`(reasoner, value) -> result`; `capabilities` is the active
`CapabilityManifest`. It also carries `registry`, `http_timeout_s`, `subflows`,
and `agents`. `DEFAULT_TASK_QUEUE` is `"julep"`.

`worker.py` registers `FlowWorkflow`, `AgentWorkflow`, and seven activity
functions. The six boundary/resolution activities are below; the seventh,
`resolveRuntimeCapabilities`, supplies deterministic run-time policy such as
`maxCalls`.

For containers there is a third entry point: `julep worker` reads
the connection and tuning knobs from the environment, resolves the
`WorkerContext` from a `WORKER_CONTEXT_FACTORY=module:attr` factory, drains
gracefully on SIGTERM, and serves `/healthz` + `/readyz` probes. That is the
Kubernetes/KEDA path — see [Kubernetes](/docs/deploy/kubernetes).

Generic workers leave `WORKER_APPLICATION` and
`WORKER_RUNTIME_DECLARATIONS_HASH` unset. The release supplies the declaration
reference to reasoner-facing activities, which hydrate it from the artifact store named by
`JULEP_ARTIFACT_STORE_URL`.

## Activities

- `verifyPures`: compare deploy-pinned pure source hashes to the worker
  registry before the workflow executes effects.
- `callTool`: invoke a native HTTP tool or MCP tool. Native tools receive
  `Idempotency-Key: <cid>`; MCP callers receive the same deterministic `cid` as
  the transport idempotency key.
- `invokeReasoner`: call the configured LLM function with a resolved `Reasoner`
  definition and input value.
- `compilePlan`: ask a planner reasoner for a plan, parse it to IR, and run staged
  plan admission before execution.
- `resolveSubflow`: resolve a subflow ref to frozen `flowJson`, `manifestJson`,
  and optional pure pins from the worker registry.
- `resolveAgentSpec`: resolve an agent controller to loop config, granted tools,
  granted contracts, and granted subflows.

Retry policy is derived per frozen `ToolContract`. Reads and native-idempotent
tools retry more liberally; non-idempotent writes retry cautiously. Policy
decisions are non-retryable: `CapabilityDenied`, `PlanRejected`,
`ValidationError`, `FreezeError`, and `PureDriftError`.

## Workflows

`FlowWorkflow` walks the frozen IR to completion. It constructs a Temporal
`Env` whose effect handlers are activities and child workflows, while the
interpreter remains the same `interpret(...)` used by the in-memory path. If
`pinned_pures` are supplied, it runs `verifyPures` before any flow effect.

`AgentWorkflow` runs the bounded `app` loop. Each round asks the controller for
one action from the closed vocabulary, checks budget, authorizes one granted
tool or subflow, records trace state, and advances. `continue_as_new` carries
config, grants, contracts, and state across segments; it truncates only the
agent workflow's history because the agent is its own child workflow.

`Sub` is a child `FlowWorkflow` resolved by ref. The Joined firewall is
structural: the child value crosses back to the parent, but the child's internal
shape and authority do not leak into the parent. See [Concepts](/docs/concepts/model)
and [SPEC §10](/docs/internals/specification#10-agent-loop).

## Human gates

`human_gate(...)` becomes a durable wait inside `FlowWorkflow`: the workflow
records an open activation id, waits on `workflow.wait_condition`, and resumes
when a client signals `submitHuman`.

```python
handle = await client.start_workflow(...)
open_gate_ids = await handle.query("openGates")
await handle.signal("submitHuman", {"cid": open_gate_ids[0], "value": {"approved": True}})
```

Two queries support a review UI:

- `openGates`: the exact activation ids currently parked on human gates.
- `projection`: an in-workflow read-only pomset snapshot with `events`,
  `costByShape`, and `pending`.

The projection query is not the durable observability sink. Control-plane runs
also egress a derived Postgres projection through regular Temporal activities;
see [Control plane](/docs/deploy/control-plane).

## Worked example

`examples/temporal_durable_agent.py` is the end-to-end local run. It uses no API
key:

1. `lookup_account` and `classify_risk` are native `@tool(effect="read",
   idempotent=True)` tools.
2. `scripted_controller(...)` is the LLM callable. It returns
   `lookup_account`, then `classify_risk`, then a final `output`.
3. `ThreadingHTTPServer` exposes the tools as stdlib HTTP tools. The handler
   accepts `POST {"input": value}` and returns JSON, matching `callTool`.
4. `WorkerContext` wires `tool_urls`, `llm=scripted_controller`, and
   `capabilities=agent.deployment().capabilities`.
5. `build_worker(...)` starts the worker on `DEFAULT_TASK_QUEUE`.
6. `agent.deploy(client, session_id="triage-run-1", input="acct-42")` starts
   the durable run.

Run it from the repository checkout:

```bash
temporal server start-dev
```

In another terminal:

```bash
.venv/bin/python examples/temporal_durable_agent.py
```

Watch `http://localhost:8233`. Open the latest `AgentWorkflow` and inspect
`invokeReasoner` / `callTool` activity history across the loop rounds. The final
stdout prints the terminal status, output, and trace.

## Debounced batch dispatch

`julep.execution.debounce` collapses a burst of single-item
submissions into one batched flow run — the Temporal counterpart of
`dbos.Debouncer`, living at the [dispatch boundary](/docs/concepts/dispatch-boundary):

```python
from julep.execution.debounce import submit_debounced

# Each call contributes one item; the collector for `key` fires after 30s of
# quiet, or at 50 items, or 5 minutes after the batch opened.
await submit_debounced(
    client, deployment.flow_json, deployment.manifest_json,
    key=f"ingest:{tenant_id}", item=item_id,
    quiet_s=30, max_items=50, max_wait_s=300,
    principal={"tenant": tenant_id, "tokenRef": cred_ref},
)
```

The target flow receives the collected list (arrival order) as its input —
typically fanning out per item with `each(...)`. The collector is a workflow
(`DebounceCollector`, registered by `build_worker`), so batches survive worker
crashes; items that arrive while a batch is executing roll into the next one
via continue-as-new. Query `pending` to see the open batch.

## Open seams

These are explicit knobs, not hidden defaults. [SPEC §6](/docs/internals/specification#6-freeze--replay-integrity)
defines the replay-integrity constraints around them.

- Freeze timing: `deploy(..., freeze_timing="deploy_time")` freezes once;
  `"per_run"` retains a snapshot source so `Deployment.refresh(...)` can
  re-freeze against fresh tool definitions.
- Retry shaping: `ExecutionPolicy` controls activity timeouts, retry attempt
  counts, backoff, and maximum retry interval.
- Continue-as-new cadence: `AgentConfig.continue_as_new_after` bounds agent
  workflow history; `0` disables the cadence.
- Projection sinks: the workflow query is replay-safe and in-memory. The
  control-plane Postgres view is activity-fed, batched, redacted, and
  best-effort; OTel remains a derived export.

Related: [docs index](/docs), [First Agent](/docs/start/first-agent),
[Kubernetes](/docs/deploy/kubernetes),
[Capabilities And Safety](/docs/guides/capabilities-and-safety), [Examples](/docs/guides/examples),
[the Typed Flow Calculus](/docs/internals/typed-flow-calculus), [the Specification](/docs/internals/specification), and
[Contributing](/docs/development/contributing).

<!-- ported-by julep-docs-site: deploy/temporal -->
