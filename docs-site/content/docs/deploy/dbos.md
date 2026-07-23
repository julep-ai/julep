---
title: "Deploy on DBOS"
description: "Durable flows and agent loops on Postgres via dbos-transact."
---

The DBOS backend (`julep.execution.dbos_backend`) runs frozen
flows on [dbos-transacthttps://docs.dbos.dev -- durable workflows
checkpointed in your existing Postgres, no extra cluster.

## Install

    pip install --pre 'julep[dbos]'    # dbos>=2.18, Python >= 3.11

## Worker wiring

Effects are configured exactly like the Temporal worker -- one process-global
`WorkerContext` -- and the backend module must be imported **before**
`DBOS.launch()` (step registration happens at import):

```python
import os

from dbos import DBOS, DBOSConfig
from julep.execution import blob_store_from_url
from julep.execution.effects import WorkerContext, configure
import julep.execution.dbos_backend as julep_dbos

blob_store = blob_store_from_url(os.environ["JULEP_BLOB_STORE_URL"])
configure(WorkerContext(
    mcp_call=my_mcp_caller,
    llm=my_llm_caller,
    blob_store=blob_store,
))
julep_dbos.set_projection_sink(my_logfire_sink)   # optional ProjectionSink

DBOS(config=DBOSConfig(name="my-app", system_database_url=DB_URL))
DBOS.launch()
```

`JULEP_BLOB_STORE_URL=file:///absolute/path` is read explicitly here: unlike
the Temporal `julep worker` host, DBOS has no Julep-owned process entrypoint.
Transcript-scoped agents with tool or subflow observations require this durable
store. Keep its root and blobs for the full lifetime of every DBOS workflow
record that can reference them. `LocalDirBlobStore` has no garbage collector or
application-level encryption; see [Agent Transcripts](/docs/internals/agent-transcripts)
for filesystem and multi-process constraints.

## Running a flow

```python
from julep.execution.dbos_backend import run_flow_dbos

result = await run_flow_dbos(
    flow_json, manifest_json,
    session_id="job-123",            # workflow id -> DBOS dedupes resubmission
    input={"q": "..."},
    queue=my_dbos_queue,             # optional: route to a DBOS queue/role
)
```

`run_flow_dbos` follows continuation segments (`continue_with`) as
`job-123`, `job-123-seg1`, `job-123-seg2`, ... carrying `maxCalls` budgets
across the chain. Human gates park on `DBOS.recv_async`; release with
`submit_human_dbos(workflow_id, cid, value)`.

## Running an agent

`app` (agent-loop) nodes run on a dedicated `julep_agent` workflow. Dispatch one
standalone with `run_agent_dbos` (the counterpart of starting Temporal's
`AgentWorkflow` directly); an `app` node inside a flow reaches the same chain
automatically through the env.

```python
from julep.execution.dbos_backend import run_agent_dbos

result = await run_agent_dbos(
    "triage_controller",                 # registered agent spec / reasoner
    session_id="agent-123",
    input={"ticket": "..."},
    config={"continueAsNewAfter": 20},   # optional overrides over the spec
    granted_tools=["kb/search"],         # optional grant attenuation
    queue=my_dbos_queue,                 # optional queue routing
)
# result: {"status", "output", "rounds", "cost", "trace", ...}
```

Segment-id convention: where Temporal calls `continue_as_new`, DBOS runs **one
workflow per history segment** -- ids `agent-123`, `agent-123-seg1`,
`agent-123-seg2`, ... A run with `continueAsNewAfter: N` starts a new segment
every N completed rounds, so a run of R rounds spans `ceil(R / N)` segments.
The whole `AgentState` (round, cost, trace, per-tool call counts) crosses
segments inside the continuation payload, so budgets and `maxCalls` span the
chain.

Gates inside agent-invoked sub-flows park in the **agent segment's** workflow:
release with `submit_human_dbos(segment_workflow_id, cid, value)` where the
cid is `f"{session_id}-sub-{round}/{gate_node_id}@{n}"` (the inline child
env's session-prefixed activation id).

Limitation: the durable session-store path (`use_session_store` /
`state_cursor`) is Temporal-only for now; on DBOS, state always crosses
segments in the continuation payload.

## Differences from the Temporal backend

| | Temporal | DBOS |
|---|---|---|
| race / hedge / quorum | supported | **rejected at dispatch** (no step cancellation) |
| `app` (agent loop) nodes | child `AgentWorkflow` + continue-as-new | inline `julep_agent` workflow per segment (`run_agent_dbos` / app nodes in flows) |
| Reasoner retries | engine retry (4 attempts) | **none -- your `LlmCaller` owns resilience** |
| Tool retries | per-contract `RetryPolicy` | quantized: idempotent 5 / write 3 attempts |
| Sub-flows | child workflow | inline in the parent workflow |
| Chaining | `continue_as_new` | one workflow per segment |
| Agent state across segments | inline or durable session store | continuation payload only (session store is Temporal-only) |
| Projection | interceptor over history | in-env emit + `set_projection_sink` |

`assert_dbos_executable(flow)` runs the rejection scan; call it at deploy time
to fail before dispatch.

## Testing note

DBOS async methods set the current event loop's default executor to DBOS's
executor; repeated `asyncio.run()` calls close that executor after the first
run, so the DBOS API spike tests reuse one module-scoped event loop.

<!-- ported-by julep-docs-site: deploy/dbos -->
