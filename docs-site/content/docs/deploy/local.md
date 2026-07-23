---
title: "Local development"
description: "Choose a service-free execution path or run the complete control-plane API locally."
---

Julep provides several local execution modes. Choose the smallest surface that
matches what you need to test:

| Mode | Best for | Services required |
|---|---|---|
| `julep run` | Fast source-level iteration from the CLI | None |
| `Deployment.dry_run(...)` | Unit tests with injected tools and reasoners | None |
| `TestClient(create_local_app(...))` | In-process control-plane and execution tests | None |
| `julep serve api --local` | Interactive API and client development | None |

The local API modes use an in-memory execution store, a local artifact
directory, and interpreter-backed execution. They do not require PostgreSQL or
Temporal. SQLite is not involved.

## Run source from the CLI

`julep run` is the quickest feedback loop for an agent or dotctx package:

```bash
julep run triage --input '{"ticket":"TICKET-42"}'
```

The default `local` environment resolves live source and runs the in-memory
interpreter with deterministic echo effects. It prints the trace tree and final
output directly. Use this mode when you do not need to exercise the HTTP API,
release records, or deployment activation.

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

With no configured API keys, local mode provides the admin token `local-dev`
when bound to a loopback host. It refuses to provide that fallback for a
non-loopback bind. Configure explicit keys before exposing the server on another
interface.

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

See [Control plane](/docs/deploy/control-plane) for production configuration and
[Temporal](/docs/deploy/temporal) for durable workflow execution.
