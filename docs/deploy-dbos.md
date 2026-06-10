# Running flows on DBOS

The DBOS backend (`composable_agents.execution.dbos_backend`) runs frozen
flows on [dbos-transact](https://docs.dbos.dev) -- durable workflows
checkpointed in your existing Postgres, no extra cluster.

## Install

    pip install 'composable-agents[dbos]'    # dbos>=2.18, Python >= 3.11

## Worker wiring

Effects are configured exactly like the Temporal worker -- one process-global
`WorkerContext` -- and the backend module must be imported **before**
`DBOS.launch()` (step registration happens at import):

```python
from dbos import DBOS, DBOSConfig
from composable_agents.execution.effects import WorkerContext, configure
import composable_agents.execution.dbos_backend as ca_dbos

configure(WorkerContext(mcp_call=my_mcp_caller, llm=my_llm_caller))
ca_dbos.set_projection_sink(my_logfire_sink)   # optional ProjectionSink

DBOS(config=DBOSConfig(name="my-app", system_database_url=DB_URL))
DBOS.launch()
```

## Running a flow

```python
from composable_agents.execution.dbos_backend import run_flow_dbos

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

## Differences from the Temporal backend

| | Temporal | DBOS |
|---|---|---|
| race / hedge / quorum | supported | **rejected at dispatch** (no step cancellation) |
| `app` (agent loop) nodes | child `AgentWorkflow` | **rejected at dispatch** (v1) |
| Brain retries | engine retry (4 attempts) | **none -- your `LlmCaller` owns resilience** |
| Hand retries | per-contract `RetryPolicy` | quantized: idempotent 5 / write 3 attempts |
| Sub-flows | child workflow | inline in the parent workflow |
| Chaining | `continue_as_new` | one workflow per segment |
| Projection | interceptor over history | in-env emit + `set_projection_sink` |

`assert_dbos_executable(flow)` runs the rejection scan; call it at deploy time
to fail before dispatch.

## Testing note

DBOS async methods set the current event loop's default executor to DBOS's
executor; repeated `asyncio.run()` calls close that executor after the first
run, so the DBOS API spike tests reuse one module-scoped event loop.
