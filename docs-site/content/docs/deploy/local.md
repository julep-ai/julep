---
title: "Local development"
description: "Choose a service-free execution path or run the complete control-plane API locally."
---

Julep provides several local execution modes. Choose the smallest surface that
matches what you need to test:

| Mode | Best for | Services required |
|---|---|---|
| `julep run` | Fast source-level iteration from the CLI | None |
| `prepare_local_pipeline(...).run/arun` | Configured production-like foreground calls | Effect dependencies only |
| `Deployment.dry_run(...)` | Unit tests with injected tools and reasoners | None |
| `TestClient(create_local_app(...))` | In-process control-plane and execution tests | None |
| `julep serve api --local` | Interactive API and client development | None |
| `julep dev up` | Durable single-machine acceptance tests | PostgreSQL, Temporal CLI, worker effects |

The local API modes use an in-memory execution store, a local artifact
directory, and interpreter-backed execution. They do not require PostgreSQL or
Temporal. SQLite is not involved.

The first five modes are **foreground** execution: they return in the caller or
API process, favor low latency, and deliberately omit crash recovery. Use them
for unit tests, prompt iteration, and foreground request paths. `julep dev up`
is the **durable** path: it exercises release publication, API persistence,
Temporal dispatch/replay, and release-scoped workers on one machine. Choosing a
local mode is a test-scope decision, not a different flow definition.

## Run source from the CLI

`julep run` is the quickest feedback loop for an agent or dotctx package:

```bash
julep run triage --input '{"ticket":"TICKET-42"}'
```

The default `local` environment resolves live source and runs the in-memory
interpreter with deterministic echo effects. It prints the trace tree and final
output directly. Use this mode when you do not need to exercise the HTTP API,
release records, or deployment activation.

## Run a configured pipeline in-process

`prepare_local_pipeline(...)` is the first-class foreground seam for an
application declared in `pyproject.toml` or `julep.toml`. It resolves the
selected environment, compiles only the named pipeline with its normal env,
policy, reasoner, freeze, and snapshot gates, and returns a reusable
`LocalPipeline` with a stable `artifact_hash`:

```python
from julep import WorkerContext, prepare_local_pipeline
from julep.llm import litellm_caller

summary = prepare_local_pipeline("episode_summary", env="local")
context = WorkerContext(llm=litellm_caller())

result = await summary.arun(
    {"episode_id": "42"},
    context=context,
    principal={"tenant": "acme"},
)
```

Prepare once when a foreground service will call the pipeline repeatedly.
`LocalPipeline.arun(...)` executes in the current event loop;
`LocalPipeline.run(...)` is the synchronous wrapper and rejects an already
running event loop. `arun_local_pipeline(...)` and `run_local_pipeline(...)`
are one-shot compile-and-run conveniences. All four execution methods return
the interpreter value directly rather than a control-plane result envelope.

The model seam is the canonical `LlmCaller(reasoner, value, principal,
transcript, dispatch)`. An explicit `llm=` wins over `WorkerContext.llm`.
`principal=` is forwarded to both model and MCP calls. MCP execution is never
inferred from ambient configuration: inject `WorkerContext(mcp_call=...)`.
QoS resolution and registry verification are also reused. A context registry
may contain the same compiled reasoner declaration, but a differing override is
rejected. Tool-calling agents additionally require a caller that accepts
Julep's optional `tools=` keyword extension.

The MCP surface is snapshotted and frozen when the pipeline is prepared, and
frozen input schemas are enforced before dispatch. This foreground seam does
not perform the control plane's per-run MCP preflight or re-snapshot drift
check; call `prepare_local_pipeline(...)` again to refresh a live surface, or
use the local/durable API when per-run preflight behavior is under test.

This path deliberately has no HTTP/control-plane hop, PostgreSQL, Temporal,
release lifecycle, or durable retry boundary. It rejects session `LOOP`
artifacts, transcript-scoped `APP` agents, staged plans, subflows, and the
reserved human-gate, sleep, recv, and emit effects with typed
`LocalExecutionUnsupported`. Ordinary business input may still contain a field
named `transcript`; only the agent runtime protocol is unsupported. Batch QoS
is clamped to foreground `FLEX`, and run-scoped control-plane secrets are not
an argument. Use `serve api --local` or a durable worker for those orchestration
surfaces.

## Unit-test a deployment

`Deployment.dry_run(...)` runs a compiled deployment in-process. Inject native
tool and reasoner implementations to test real application logic without a
worker or control plane:

```python
deployment = deploy(flow, tools=[lookup_ticket])

result = deployment.dry_run(
    {"ticket": "TICKET-42"},
    tools={"lookup_ticket": fake_lookup_ticket},
    reasoners={"triage": fake_triage},
)

assert result.value == {"priority": "high"}
```

For an MCP-backed deployment, pass `mcp_call=...` or an injected implementation
through `tools`. This is the most focused option for unit tests; it does not
exercise the release or run API.

## Test the API in-process

Use `create_local_app(...)` with Starlette's `TestClient` to exercise the same
HTTP routes without opening a port:

```python
from starlette.testclient import TestClient

from julep.server import create_local_app


app = create_local_app(project_root=tmp_path)

with TestClient(app) as client:
    response = client.get(
        "/v1/ready",
        headers={"Authorization": "Bearer local-dev"},
    )
    assert response.status_code == 200
```

The factory stores artifacts under `<project>/.julep/artifacts`. Runs, release
records, deployment records, projections, gates, and vault rows otherwise live
only in the process and disappear when the application exits.

With no configured API keys, echo-only local mode provides the admin token
`local-dev` when bound to a loopback host. It refuses to provide that fallback
for a non-loopback bind. Configured-context mode can invoke real effects and
therefore requires explicit API keys even on loopback.

Only one local-app lifespan may be active in a process at a time. Local mode
temporarily owns process-wide effect and artifact resolution; an overlapping
`TestClient` lifespan fails immediately instead of risking cross-app context or
credential leakage. Use one shared app in a test process or put independent
local apps in separate processes.

## Serve the local API

Run the same application under Uvicorn for interactive testing or development
against an HTTP client:

```bash
pip install --pre 'julep[server]'
julep serve api --local --host 127.0.0.1 --port 8080
```

`--local` cannot be combined with `--migrate`: the local execution store has no
database schema to migrate.

By default, the server uses deterministic echo effects. Supply a zero-argument
sync or async factory returning a `WorkerContext` to call configured tools and
reasoners instead:

```bash
LOCAL_JULEP_TOKEN="$(openssl rand -hex 32)"
export JULEP_API_KEYS="local-admin:${LOCAL_JULEP_TOKEN}:admin"
julep serve api --local \
  --context-factory my_project.worker:build_context
```

Configured-context execution uses the normal effect implementations, including
real MCP discovery, binding validation, and preflight. Echo execution makes no
network calls: it simulates an MCP surface equal to the tools frozen into the
release. Because echo mode has no real secret transport or binding to validate,
it rejects runs that submit run-scoped secrets.

## Exercise the release lifecycle

The local server preserves the normal control-plane sequence:

1. Upload referenced blobs with `PUT /v1/artifacts/{sha256}`.
2. Publish the immutable application release with `POST /v1/releases`.
3. Activate it on a lane with `POST /v1/deployments`.
4. Start a pipeline with `POST /v1/runs`.
5. Read events, open gates, signals, status, and the terminal result through the
   ordinary `/v1/runs/{run_id}/...` endpoints.

This means an HTTP client can use the same artifact, release, deployment, and
run flow locally before it targets a durable control plane. Queue names remain
part of release metadata, but the process-local gateway does not dispatch work
to external queues.

## Run the durable stack on one machine

Use the supervised development stack when the behavior under test includes
idempotent submission, PostgreSQL run records, Temporal retry/replay, payload
encryption, or worker queue routing.

Install the server/store/Temporal dependencies, a local PostgreSQL server, and
the Temporal CLI. Generate independent development-only admin API, worker API,
payload-codec, vault, and signing keys, then load the file into the supervisor:

```bash
pip install --pre 'julep[server,store]'
mkdir -p .julep
julep keygen --output .julep/dev.env
source .julep/dev.env

export JULEP_EXECUTION_STORE_DSN='postgresql://postgres:postgres@127.0.0.1:5432/julep'
```

`julep keygen` writes mode `0600`, refuses to replace an existing file unless
`--force` is supplied, and prints shell exports to stdout when `--output` is
omitted. Use `--format json` when feeding a secret manager instead of a shell.
The generated values are local credentials; Julep does not persist them for
you and they should not be committed.

The supervisor partitions that input by process. Publication receives the
private signing seed; the API receives the static API keyring and vault keys;
workers receive the shared payload codec, public signer allow-list, and only
the worker-role token as `JULEP_API_KEY`. Workers never receive
`JULEP_API_KEYS`, vault decryption keys, the admin token, or the private signing
seed. `JULEP_WORKER_API_KEY` exists only as the supervisor's handoff name; it is
used for authenticated vault reads through `JULEP_API_URL`.

Configure a local file release store, the worker context factory that supplies
real effects, and the lane queues in `julep.toml`:

```toml
[env.local]
temporal_address = "127.0.0.1:7233"
release_store = "file:///absolute/path/to/project/.julep/releases"
worker_context_factory = "my_project.worker:build_context"

[env.local.queues]
default = "julep-local"
reasoner = "julep-local-reasoner"
```

Start the complete stack in the foreground:

```bash
julep dev up --env local
```

The supervisor starts Temporal's local dev server, migrates and starts the
durable API, publishes and registers the configured application through the
Python API, and starts one worker for every release-scoped lane queue. It waits
for dependency readiness and tears down all child processes on exit. The API
is loopback-only in this mode.

Use `--no-start-temporal` to connect to an already-running local Temporal
frontend, `--no-publish --no-worker` to bring up infrastructure only, and
`--dry-run` to inspect the redacted process plan. `--api-url` defaults to
`JULEP_API_URL`, then `http://127.0.0.1:8080`; `--api-key` defaults to
`JULEP_API_KEY`. The selected key must match an admin entry in
`JULEP_API_KEYS`; the generated `JULEP_WORKER_API_KEY` must match its separate
worker-role entry.

This mode still uses PostgreSQL and Temporal intentionally. If a test only
needs the HTTP surface, use `create_local_app(...)` or `serve api --local`
instead of replacing PostgreSQL with another database.

## Limitations

Local API mode is an early-iteration and testing surface, not a deployment
backend:

- State is process-local and is not recovered after exit or a crash.
- It does not provide Temporal replay durability or multi-process execution.
- Configured effects run locally without Temporal's activity retry, QoS, or
  timeout scheduling semantics.
- It does not run Helm reconciliation or production workers.
- Session `LOOP` artifacts are not supported; use a finite flow.
- Use the PostgreSQL and Temporal control plane for durable, distributed runs.

The foreground limitations above do not apply to `julep dev up`; that command
runs the real durable components, but remains a single-machine development
supervisor rather than a production process manager.

See [Control plane](/docs/deploy/control-plane) for production configuration and
[Temporal](/docs/deploy/temporal) for durable workflow execution.
