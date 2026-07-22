---
title: "Control plane"
description: "Self-hosted release, deployment, run, projection, and administration API."
---

The optional control plane is a FastAPI application over Postgres, a artifact store, and
Temporal. It publishes immutable releases, records lane activation, starts
workflows, and serves the derived execution projection. It does not replace
Temporal as the durability mechanism.

## Install and run

```bash
pip install --pre 'julep[server]'
julep serve api --host 127.0.0.1 --port 8080 --migrate
```

The `server` extra installs FastAPI, Uvicorn, sse-starlette,
`psycopg[binary,pool]`, Temporal, cryptography, and httpx. `julep serve api`
builds `ServerSettings.from_env()`, optionally applies the Postgres migrations,
constructs the app, and runs Uvicorn.

## Configuration

Environment variables override `[server]` in `julep.toml`, which overrides
`[tool.julep.server]` in `pyproject.toml`.

| Variable | Default | Meaning |
|---|---|---|
| `JULEP_API_KEYS` | empty | Comma- or whitespace-separated `name:token[:admin]` keys. |
| `JULEP_EXECUTION_STORE_DSN` | none | PostgreSQL DSN. Required to serve the API. |
| `JULEP_ARTIFACT_STORE_URL` | `file://<project>/.julep/artifacts` | Release and runtime-declaration artifact store. |
| `TEMPORAL_ADDRESS` | `localhost:7233` | Temporal frontend. |
| `TEMPORAL_NAMESPACE` | `default` | Temporal namespace. |
| `TEMPORAL_TASK_QUEUE` | `julep` | Default task queue. |
| `TEMPORAL_API_KEY` | unset | Temporal Cloud API key. |
| `TEMPORAL_TLS` | true iff API key set | Force Temporal TLS on or off. |
| `TEMPORAL_PAYLOAD_KEYS` | unset | Payload-codec keyring. Set with `TEMPORAL_PAYLOAD_KEY_ID`. |
| `TEMPORAL_PAYLOAD_KEY_ID` | unset | Active payload-codec key id. |
| `TEMPORAL_PAYLOAD_ENCRYPTION_REQUIRED` | `true` | Require encrypted control-plane workflow starts. Set `false` only for a trusted plaintext Temporal deployment. |
| `JULEP_SERVER_HOST` | `127.0.0.1` | Listen host. |
| `JULEP_SERVER_PORT` | `8080` | Listen port. |
| `JULEP_PROJECTION_BATCH_SIZE` | `20` | Projection events per activity batch. |
| `JULEP_PROJECTION_BATCH_INTERVAL_S` | `2.0` | Maximum projection batch interval. |
| `JULEP_SERVER_RECONCILE_INTERVAL_S` | `60` | Run reconciliation interval. `0` disables the loop. |
| `JULEP_SERVER_HELM_CHART` | unset | Enable Helm lane reconciliation with this chart. |
| `JULEP_SERVER_KUBERNETES_NAMESPACE` | `julep` | Helm reconciliation namespace. |
| `JULEP_SERVER_WORKER_CONTEXT_FACTORY` | unset | Worker `module:attribute` context factory. Required with Helm reconciliation. |
| `JULEP_SERVER_PAYLOAD_ENCRYPTION_SECRET` | unset | Kubernetes payload-codec Secret. Required with Helm reconciliation. |
| `JULEP_SERVER_WORKER_SERVICE_ACCOUNT` | unset | Existing worker ServiceAccount. |
| `JULEP_SERVER_WORKER_PRIORITY_CLASS` | unset | Existing worker PriorityClass. |

The server table recognizes `api_keys`, `execution_store_dsn`, `artifact_store_url`,
`temporal_address`, `temporal_namespace`, `temporal_task_queue`,
`temporal_api_key`, `temporal_tls`, `temporal_payload_keys`/`payload_keys`,
`temporal_payload_key_id`/`payload_key_id`,
`temporal_payload_encryption_required`/`payload_encryption_required`, `host`,
`port`, `projection_batch_size`, `projection_batch_interval_s`,
`reconcile_interval_s`, `helm_chart`, `kubernetes_namespace`,
`worker_context_factory`, `payload_encryption_secret`,
`worker_service_account`, `worker_priority_class`, and `queue_by_lane`.

## Authentication and ownership

Every route except `GET /v1/health` requires `Authorization: Bearer <token>`;
`GET /v1/ready` also requires a bearer key. The keyring compares every candidate with
`hmac.compare_digest` and yields an `ApiKey(name, principal_base, admin)`.

Admin keys are required for:

- `PUT /v1/artifacts/{sha256}`
- `POST /v1/releases`
- `POST /v1/deployments`

Run lists, records, controls, values, gates, and events are owner-scoped for
non-admin keys. Every field in the key's `principal_base` must match the run's
principal; admins bypass this check. A submitted principal may add metadata but
cannot change a key-owned field. A conflicting value returns `400`.

Send `SIGHUP` to reload configured keys. Tokens are excluded from diagnostics.
Terminate TLS at the ingress; the application assumes a secure transport.

## Endpoints

### Health

```http
GET /v1/health HTTP/1.1
```

Unauthenticated liveness returns `200`:

```json
{"status":"ok"}
```

Authenticated `GET /v1/ready` checks Postgres, artifact store, and Temporal. It returns
`200` with `status: "ready"`, or `503` with `status: "unavailable"`; `checks`
maps each dependency to `ok` or an error class.

### artifact store

```http
PUT /v1/artifacts/<64-lowercase-hex> HTTP/1.1
Authorization: Bearer <admin-key>
Content-Type: application/octet-stream

<blob bytes>
```

The server recomputes SHA-256. A new blob returns `201`, an existing blob
returns `200`, and a digest mismatch returns `400`. `HEAD /v1/artifacts/{sha256}`
accepts any key and returns `200` when present or `404` when absent.

### Releases

```http
POST /v1/releases HTTP/1.1
Authorization: Bearer <admin-key>
Content-Type: application/json

<raw schema-v2 ApplicationRelease JSON>
```

The request body is the raw release manifest. The server parses schema version
2, recomputes `release_hash`, verifies every referenced bundle and runtime
declaration blob in artifact store, and stores the manifest. Missing blobs return `409`
with their digests. A new release returns `201`; an existing release returns
`200`.

`GET /v1/releases?cursor=...&limit=50` accepts any key and returns
`{"items": [...], "next_cursor": ...}`. `limit` is `1..100`.
`GET /v1/releases/{hash}` accepts either bare hex or `sha256:<hex>`.

### Deployments

```http
POST /v1/deployments HTTP/1.1
Authorization: Bearer <admin-key>
Content-Type: application/json

{"lane":"summaries","release":"sha256:<digest>"}
```

The lane must be declared by the release or the request returns `400`. The
response contains the deployment row and `reconcile`. With
`JULEP_SERVER_HELM_CHART`, activation reconciles the lane worker. Without it,
`reconcile.status` is `external`: activation records routing and worker rollout
remains external.

`GET /v1/deployments` accepts any key and returns `{"items": [...]}` with the
current reconcile status for every lane.

Activation replaces the active release for a lane. Rollback is the same
operation with a prior release on that lane.

### Runs

```http
POST /v1/runs HTTP/1.1
Authorization: Bearer <key>
Idempotency-Key: summarize-episode-42
Content-Type: application/json

{
  "pipeline": "episode-summary",
  "input": {"episode_id": "42"},
  "sessionId": "episode-42",
  "principal": {"tenant": "acme"},
  "queueLanes": {"reasoner": "summaries"}
}
```

The body accepts `release`, `pipeline`, `input`, `sessionId`, `principal`,
`queueLanes`, and `runId`. Supply either the `Idempotency-Key` header or
`runId`; omitting both returns `400`. When `release` is omitted, the server
resolves the pipeline from active deployments. No match returns `404`; matches
in more than one deployment return `409`.

The workflow id is `run-<run_id>`. Without `runId`, `run_id` is a UUIDv5 of the
idempotency key. A fresh submission returns `201`. A duplicate returns its
existing run with `200` for its owner; reuse by a different owner returns
`409`.

Submission crosses a non-atomic Postgres-insert to Temporal-start boundary.
The state transition is `submitting` to `accepted`, then `running` after the
first projection event. A failed start becomes `start_failed`, a terminal
submission failure with no workflow. Workflow terminal states are `completed`,
`failed`, `canceled`, and `terminated`.

The background reconciler repairs the boundary every
`JULEP_SERVER_RECONCILE_INTERVAL_S`: a `submitting` workflow that is absent
becomes `start_failed`, one that is running becomes `accepted`, and a terminal
one is patched terminal. It also patches stuck `accepted` and `running` rows
from Temporal state.

Run query and control routes are owner-scoped:

| Route | Result |
|---|---|
| `GET /v1/runs?cursor=...&limit=50` | Cursor page, `limit` `1..100`; admins see all. |
| `GET /v1/runs/{id}` | One run. |
| `POST /v1/runs/{id}/cancel` | `{"status":"cancel_requested"}`. |
| `POST /v1/runs/{id}/terminate` | `{"status":"terminate_requested"}`. |
| `GET /v1/runs/{id}/result?wait_s=N` | `N` is `0..60`; terminal returns `200 {run,result}`, otherwise `202 {run}`. |
| `GET /v1/runs/{id}/values/{value_ref}` | Claim-checked value; `404` if unreferenced, absent, or oversize. |
| `GET /v1/runs/{id}/gates` | `{"gates":[...]}` with open human-gate cids. |
| `POST /v1/runs/{id}/signals/human` | Body `{"cid":"...","value":...}`; delivers `submitHuman` and returns `{"status":"delivered"}`. |

### Run events

Without `Accept: application/json`, `GET /v1/runs/{id}/events` returns
`text/event-stream`. Every durable row is encoded as:

```text
event: projection
id: 17
data: {"attrs":{},"cid":"...","seq":17,"type":"Did"}
```

`data` is the canonical-JSON projection row. Resume with `Last-Event-ID` or
`?after=<seq>`. The server emits an initial keep-alive comment and repeats it
every 15 seconds, reads at most 500 rows per page, and disconnects a client
whose send blocks for 30 seconds. The terminal event is read from the
atomically-written durable terminal row; it is never synthesized.

With `Accept: application/json`, the same route returns a page:

```json
{"items":[],"next_cursor":null}
```

Use `after` and `limit`; `limit` is at most 500.

## Store administration and projection semantics

```bash
julep db migrate
julep db migrate --dsn postgresql://user:pass@host/db
julep db sweep --older-than 604800
julep serve api --migrate
```

`db migrate` applies numbered, idempotent migrations and defaults to
`JULEP_EXECUTION_STORE_DSN`. The schema contains `runs`, `projection_events`,
`projection_values`, `releases`, `deployments`, and `schema_migrations`.
`serve api --migrate` applies the same schema before startup. Worker processes
do not migrate the schema; run `db migrate` as an operator-controlled init job
before enabling projection egress.

`db sweep` deletes projection events and unreferenced values for terminal runs
older than the supplied seconds. Retention is operator policy.

Projection egress uses regular Temporal activities with at-least-once delivery
and batched writes. Database conflict keys make identical retries idempotent.
Values are redacted before their durable reference is computed. Oversize values
retain an oversize marker but drop the payload. The projection is a derived,
best-effort view, not workflow durability. See the repository's
`docs/observability.md` for redaction configuration.

## Clients

`julep.client.JulepClient` is a small synchronous httpx client installed by
`julep[http]`. For terminal reads:

```bash
julep status --remote --api-url https://julep.example --api-key "$JULEP_API_KEY"
julep trace --remote <run_id> --api-url https://julep.example --api-key "$JULEP_API_KEY"
```

The CLI also reads `JULEP_API_URL` and `JULEP_API_KEY`. See
[schema-v2 releases](/docs/deploy/temporal#self-contained-schema-v2-releases)
for the artifacts accepted by the release endpoint.
