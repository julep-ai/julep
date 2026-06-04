# Deploy to Temporal

The durable path runs the same admitted artifact as the local interpreter: a
frozen `flow_json`, a frozen `manifest_json`, pinned pure source hashes, brain
identity, capability manifest, framework version, and an `artifact_hash`. Only
the injected `Env` changes. Local tests use in-memory callables; Temporal uses
workflows, activities, child workflows, durable signals, and activity retry
policy. See [README.md](../README.md#execution-on-temporal) and
[SPEC §6](SPEC.md#6-freeze--replay-integrity).

## Prereqs

Run a Temporal dev server:

```bash
temporal server start-dev
```

Install the Temporal extra:

```bash
pip install 'composable-agents[temporal]'
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
from composable_agents import deploy

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

## Standing up a worker

The worker host is the process that connects environment-specific capability to
the deterministic workflows. Use `build_worker(...)` when you own the
`temporalio.client.Client`; use `run_worker(...)` for a standalone process.

```python
from temporalio.client import Client
from composable_agents.execution.activities import WorkerContext
from composable_agents.execution.worker import DEFAULT_TASK_QUEUE, build_worker

client = await Client.connect("localhost:7233")
context = WorkerContext(
    hand_urls={"send_email": "https://hands.example/send_email"},
    mcp_call=my_async_mcp_caller,
    llm=my_async_llm,
    capabilities=caps,
    subflows={},
    agents={},
)
worker = build_worker(client, context, task_queue=DEFAULT_TASK_QUEUE)
await worker.run()
```

`WorkerContext` fields are process-global activity configuration: `hand_urls`
maps native hand names to HTTP URLs; `mcp_call` is async
`(server, tool, value, idempotency_key) -> result`; `llm` is async
`(brain, value) -> result`; `capabilities` is the active
`CapabilityManifest`. It also carries `registry`, `http_timeout_s`, `subflows`,
and `agents`. `DEFAULT_TASK_QUEUE` is `"composable-agents"`.

`worker.py` registers `FlowWorkflow`, `AgentWorkflow`, and seven activity
functions. The six boundary/resolution activities are below; the seventh,
`resolveRuntimeCapabilities`, supplies deterministic run-time policy such as
`maxCalls`.

## Activities

- `verifyPures`: compare deploy-pinned pure source hashes to the worker
  registry before the workflow executes effects.
- `callHand`: invoke a native HTTP hand or MCP tool. Native hands receive
  `Idempotency-Key: <cid>`; MCP callers receive the same deterministic `cid` as
  the transport idempotency key.
- `invokeBrain`: call the configured LLM function with a resolved `Brain`
  definition and input value.
- `compilePlan`: ask a planner brain for a plan, parse it to IR, and run staged
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
shape and authority do not leak into the parent. See [concepts.md](concepts.md)
and [SPEC §10](SPEC.md#10-agent-loop).

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

The projection query is not the durable observability sink. [SPEC §11](SPEC.md#11-projection)
requires durable projection sinks to be derived out-of-band from history.

## Worked example

`examples/temporal_durable_agent.py` is the end-to-end local run. It uses no API
key:

1. `lookup_account` and `classify_risk` are native `@tool(effect="read",
   idempotent=True)` hands.
2. `scripted_controller(...)` is the LLM callable. It returns
   `lookup_account`, then `classify_risk`, then a final `output`.
3. `ThreadingHTTPServer` exposes the tools as stdlib HTTP hands. The handler
   accepts `POST {"input": value}` and returns JSON, matching `callHand`.
4. `WorkerContext` wires `hand_urls`, `llm=scripted_controller`, and
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
`invokeBrain` / `callHand` activity history across the loop rounds. The final
stdout prints the terminal status, output, and trace.

## Open seams

These are explicit knobs, not hidden defaults. [SPEC §6](SPEC.md#6-freeze--replay-integrity)
defines the replay-integrity constraints around them.

- Freeze timing: `deploy(..., freeze_timing="deploy_time")` freezes once;
  `"per_run"` retains a snapshot source so `Deployment.refresh(...)` can
  re-freeze against fresh tool definitions.
- Retry shaping: `ExecutionPolicy` controls activity timeouts, retry attempt
  counts, backoff, and maximum retry interval.
- Continue-as-new cadence: `AgentConfig.continue_as_new_after` bounds agent
  workflow history; `0` disables the cadence.
- Projection sinks: the workflow query is replay-safe and in-memory. Durable
  sinks such as Postgres or OTel are fed from history outside the workflow.

Related: [docs index](README.md), [getting-started.md](getting-started.md),
[capabilities-and-safety.md](capabilities-and-safety.md), [examples.md](examples.md),
[design/typed-flow.md](design/typed-flow.md), [SPEC.md](SPEC.md), and
[CONTRIBUTING.md](../CONTRIBUTING.md).
