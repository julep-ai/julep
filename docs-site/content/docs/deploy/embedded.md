---
title: "Embedded execution"
description: "Call one Julep pipeline in your own process, inside your own workflow engine, with no Julep services."
---

Embedded execution runs one configured Julep pipeline as a normal function call
in your process. There is no Temporal, no PostgreSQL, no Julep server, no
release publication, and no Kubernetes. The public entry point is
`prepare_local_pipeline(...)` plus `LocalPipeline.arun(...)`.

This is the path to use when your application already has a workflow engine —
DBOS, Temporal, Celery, Airflow, or a plain request handler — and you want Julep
to own the prompt rather than the orchestration.

## The admission rule

**Use embedded Julep for prompt calls. Use remote durable Julep when Julep
replaces your orchestration.**

Concretely: if your own engine stays the outer loop and Julep performs one
*think*, embedded execution is enough. Prepare the pipeline once, call it per
request or per step, and keep your existing retries, checkpoints, and telemetry.

Move to the durable control plane when Julep owns the run's lifecycle: multi-step
agent loops with tools, durable waits, fan-out, human gates, or an execution
identity that must outlive your process. Those shapes need release records, run
records, replay, and gate transport — see [Control plane](/docs/deploy/control-plane)
and [Temporal](/docs/deploy/temporal).

| Your situation | Path |
|---|---|
| One model call inside a step you already own | Embedded (`prepare_local_pipeline`) |
| Prompt with a frozen output schema, called from a request handler | Embedded |
| Agent loop with tools, rounds, and budgets | Durable control plane |
| Durable sleeps, human gates, signals, session loops | Durable control plane |
| Run must be inspectable and resumable after your process dies | Durable control plane |

Embedded and durable execution compile the *same* pipeline definition through the
same application compiler, env profile, policy, freeze, and snapshot gates. Choosing
embedded is a deployment decision, not a different flow definition.

## Run a configured pipeline in-process

`prepare_local_pipeline(...)` resolves your Julep config, compiles only the named
pipeline, and returns a reusable `LocalPipeline` with a stable `artifact_hash`:

```python
from julep import WorkerContext, prepare_local_pipeline
from julep.llm import litellm_caller

summary = prepare_local_pipeline("episode_summary", env="local")
context = WorkerContext(llm=litellm_caller())

value = await summary.arun({"episode_id": "42"}, context=context)
```

The full signatures:

```python
prepare_local_pipeline(
    pipeline: str,
    *,
    project_root: str | Path = ".",
    config: JulepConfig | None = None,
    env: str = "local",
) -> LocalPipeline

await pipeline.arun(input=None, *, llm=None, context=None, principal=None) -> Any
pipeline.run(input=None, *, llm=None, context=None, principal=None) -> Any
```

Prepare once and reuse the object: compilation is the expensive part, and every
call on one `LocalPipeline` shares its frozen `artifact_hash`. `arun(...)`
executes in the current event loop; `run(...)` is the synchronous wrapper and
raises `LocalExecutionConfigurationError` if an event loop is already running.
`arun_local_pipeline(...)` and `run_local_pipeline(...)` are one-shot
compile-and-run conveniences that take the same `project_root` / `config` / `env`
keywords; they recompile on every call, so they are for scripts and tests rather
than a hot path.

Effects are always explicit. A pipeline that invokes a reasoner needs a model
seam — pass `llm=` or `WorkerContext(llm=...)`, where an explicit `llm=` wins
over the context's — otherwise `arun` raises
`LocalExecutionConfigurationError`. `julep.llm.litellm_caller()` is the built-in
implementation of the canonical seam
`LlmCaller(reasoner, value, principal, transcript, dispatch, *, tools=None)`;
it accepts `request_timeout_s=` and an injectable `acompletion=`. A pipeline that
binds MCP tools needs `WorkerContext(mcp_call=...)`; MCP transport is never
inferred from ambient configuration. `principal=` is forwarded to both model and
MCP calls.

What embedded execution needs at runtime: your model provider credentials and
nothing else. What it does not need: Temporal, PostgreSQL, a Julep API process, a
published release, an activated deployment, or Kubernetes.

## Embed without a Julep project file

`prepare_local_pipeline` reads `pyproject.toml` / `julep.toml` by default. If you
own a `.ctx` package but no Julep project file, build the same configuration
objects in memory and pass them as `config=`:

```python
from pathlib import Path

from julep import WorkerContext, prepare_local_pipeline
from julep.cli.config import EnvConfig, JulepConfig
from julep.ctx_pipeline import CtxPipelineConfig
from julep.llm import litellm_caller

root = Path(__file__).parent            # anchors relative `ctx` paths
config = JulepConfig(
    root=root,
    envs={"prod": EnvConfig(name="prod", vars={"SUMMARY_MODEL": "openai/gpt-5.4-nano@medium"})},
    pipelines={
        "episode_summary": CtxPipelineConfig(
            name="episode_summary",
            ctx="episode_summary.ctx",
        ),
    },
)

summary = prepare_local_pipeline("episode_summary", config=config, env="prod")
value = await summary.arun(
    {"episode_id": "42"},
    context=WorkerContext(llm=litellm_caller()),
)
```

Three things this recipe depends on:

- `JulepConfig.root` anchors a relative `CtxPipelineConfig.ctx` path; an absolute
  `ctx` is used as-is.
- The `env=` you pass must be a key of `JulepConfig.envs`, or
  `prepare_local_pipeline` raises `LocalPipelineNotFound` listing the configured
  environments. The default is `"local"`.
- `EnvConfig.vars` (merged with `EnvConfig.worker_environment`, then with
  `CtxPipelineConfig.env`) is the environment bound to your package's dotctx
  expressions — the `$env.get(...)` defaults in `settings.yaml` read from it, not
  from the ambient process environment.

`CtxPipelineConfig` also carries `tools` (prompt-visible alias → `server:tool`
wire target), `policy`, `context_max_tokens`, `summarizer`, and `lane`. A
tool-less prompt needs none of them. When a `JulepConfig` declares only ctx
pipelines and no `application`, Julep synthesizes the application from those
pipelines, so a code-defined `Application` is not required.

This is the supported no-project-file path today, and it is admittedly
control-plane vocabulary for what is really a prompt call. A first-class
`julep.embedded.load_pipeline(path, env=...)` — load a `.ctx` directory, compile
one tool-less pipeline, return a `LocalPipeline` — is planned. `julep.embedded`
does not exist yet; use the recipe above until it does.

## What embedded execution accepts

The embedded path is a real subset of the IR, checked before any effect runs
(`_assert_foreground_supported` in `julep/local.py`). Treat this as a contract you
design against, not a runtime surprise. Every rejection raises
`LocalExecutionUnsupported` (a subclass of `LocalPipelineError`, itself a
`JulepError`):

| Rejected shape | Why |
|---|---|
| Session `LOOP` flows | Needs a durable session boundary |
| Staged plans (`EVAL_PLAN`) | Needs the control plane's plan staging |
| `APP` agent nodes with `whole_session` or `summary` context scope | Needs transcript materialization and budgeting |
| `APP` agent nodes with subflows | Embedded execution does not resolve agent subflows |
| Subflow steps (`sub(...)`) | Embedded execution does not resolve subflows |
| The reserved effects `__human_gate__`, `__sleep__`, `__recv__`, `__emit__` | Need a durable retry/park boundary |

Everything else compiles and runs, including finite flows, native tools, MCP
tools (with an injected `mcp_call`), and non-transcript agent rounds with frozen
native tool definitions.

Two further behaviors to know:

- `BATCH` QoS is clamped to `FLEX` for embedded calls, because batch dispatch
  needs a durable submit/wait boundary. The resolved tier otherwise comes from
  `WorkerContext.resolve_qos` exactly as it does on a worker.
- The MCP surface is snapshotted and frozen when the pipeline is prepared.
  Embedded execution does not run the control plane's per-run MCP preflight or
  re-snapshot drift check; call `prepare_local_pipeline(...)` again to refresh.

An ordinary business input field named `transcript` is fine — only the agent
runtime's transcript protocol is unsupported.

## Observability: what you get today

**`LocalPipeline.arun` returns the interpreter's unwrapped value and nothing
else.** The interpreter's result carries a projection event id, attribute
metadata, and reported cost, and the run builds an in-memory projection — none of
that is returned to the caller or forwarded to a sink. Attempt counts, token
usage, cost, and the artifact identity of the specific call are not observable
from the return value. `WorkerContext.on_attempt` is a worker-activity seam and is
not invoked on this path.

Do not plan embedded adoption around Julep-side tracing. What you can do today:

- **Own the model-call telemetry.** Inject your own `LlmCaller` instead of
  `litellm_caller()`. It receives the rendered `Reasoner`, the input value, the
  `principal`, and the `ReasonerDispatch` (including the resolved QoS tier), and it
  returns the provider response — so latency, tokens, cost, retries, and prompt
  identity are all recordable in your existing instrumentation, at the seam you
  control.
- **Record the deployment identity yourself.** `LocalPipeline.artifact_hash`,
  `.name`, and `.environment` are stable for the prepared object; log them
  alongside your own step id.

An optional result envelope and a projection sink for embedded runs are planned,
and would not change the value-only default of `arun`. Until then, a complete
Julep-side execution trace requires the durable backends: Temporal's projection
interceptor, or DBOS's `set_projection_sink` (see [Deploy on DBOS](/docs/deploy/dbos)).

## Durability: who owns the workflow

Both shapes below give you durable execution on DBOS. They differ in who owns the
workflow record, and that is the architecture boundary worth being explicit about.

### (a) Recommended for a single-shot prompt: your step, Julep's prompt

Call `LocalPipeline.arun` inside a step you already own. DBOS checkpoints *your*
step; Julep contributes one model call and no workflow records of its own.

```python
from dbos import DBOS

from julep import WorkerContext, prepare_local_pipeline
from julep.llm import litellm_caller

SUMMARY = prepare_local_pipeline("episode_summary", env="prod")
CONTEXT = WorkerContext(llm=litellm_caller())


@DBOS.step()
async def summarize_episode(episode_id: str) -> dict:
    return await SUMMARY.arun({"episode_id": episode_id}, context=CONTEXT)


@DBOS.workflow()
async def ingest_episode(episode_id: str) -> dict:
    summary = await summarize_episode(episode_id)
    return await persist_summary(episode_id, summary)   # your own step
```

Your workflow keeps the retry policy, the checkpoint granularity, the
idempotency key, and the trace. Prepare the pipeline at module import, not per
call. This is the shape to use when Julep performs one *think* inside your
orchestration.

### (b) Julep owns the orchestration: `run_flow_dbos`

`run_flow_dbos` starts a Julep-owned DBOS workflow for a frozen flow. It runs
`assert_dbos_executable(...)` first, opens a trajectory record for the run,
dispatches each effect through registered `@DBOS.step` functions (so every effect
is separately checkpointed and retried per contract), follows `continue_with`
continuation segments as `job-123`, `job-123-seg1`, `job-123-seg2`, ... carrying
`maxCalls` budgets across the chain, and closes the trajectory as completed or
failed.

```python
from julep.execution.dbos_backend import run_flow_dbos

result = await run_flow_dbos(
    flow_json,
    manifest_json,
    session_id="job-123",        # workflow id -> DBOS dedupes resubmission
    input={"episode_id": "42"},
    queue=my_dbos_queue,         # optional queue/role routing
)
```

This requires the DBOS worker wiring — a process-global `WorkerContext` via
`configure(...)`, the backend module imported before `DBOS.launch()`, and a blob
store for transcript-scoped agents. See [Deploy on DBOS](/docs/deploy/dbos).

**The tradeoff.** For a one-model-call prompt, `run_flow_dbos` adds a nested
Julep-owned workflow, its own workflow id namespace, trajectory records, and
per-effect step checkpoints *around* a call your own step is already
checkpointing. That machinery is worth it when Julep owns the orchestration —
multi-step flows, human gates, durable waits, agent loops, continuation chains.
It is overhead when it does not. Pick (a) for prompts and (b) for orchestration.

## Related

- [Local development](/docs/deploy/local) — the other service-free modes, and how
  embedded execution compares to `julep run`, `Deployment.dry_run`, and the local
  API.
- [Deploy on DBOS](/docs/deploy/dbos) — durable flows and agent loops on Postgres.
- [Control plane](/docs/deploy/control-plane) — releases, deployments, and run
  records for the durable path.
- [Python API](/docs/reference/python-api) — signatures for
  `prepare_local_pipeline`, `LocalPipeline`, and the effect seams.
