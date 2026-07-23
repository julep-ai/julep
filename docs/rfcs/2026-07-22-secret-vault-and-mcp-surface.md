# RFC: Secret vault (lite), MCP surface contract, and dotctx agents on AgentWorkflow

- **Status:** final draft
- **Owner:** Diwank Singh Tomer
- **Date:** 2026-07-22
- **Depends on:** the `julep3-post-port` program (control plane `/v1`, schema-v2 releases with
  `runtimeDeclarationsRef`, `mcp_tool()` + snapshot-at-freeze, `julep.mcp_auth`, redaction
  wiring, the CAS→artifacts rename)

## 1. Motivation

Three gaps, surfaced by the mem-mcp port and the CMA credential-vault research:

1. **Secrets are literal strings.** MCP server auth headers live verbatim in
   `[tool.julep.mcp.servers.*.headers]`; provider keys arrive as ambient worker env; the only
   managed path is Helm's `worker_secret_environment` → K8s `secretKeyRef` (K8s-only, restart
   to rotate, no local-dev story).
2. **The frozen MCP tool surface is unenforced.** Freezing snapshots `tools/list` and derives
   conservative contracts from `McpAnnotations`, but nothing checks that the live server still
   matches that surface at run time — drift surfaces as an opaque mid-run activity failure.
   `_retry_policy_for` (`execution/harness.py`) also chooses retry counts
   from the tool contract **without checking `FrozenTool.asserted`** — an MCP server can claim
   `idempotentHint: true` and obtain retries it is not entitled to. MCP annotations are
   untrusted hints by spec.
3. **dotctx agents cannot run zero-code.** `AgentWorkflow` (`julep/agent_loop.py`,
   `execution/harness.py:2132+`) is already a durable, bounded, native tool-calling loop with
   deterministic activity cids, contract-aware dispatch (READ calls concurrent, writes
   serialized), `require_tool_call`, and mid-loop continue-as-new — but a dotctx reasoner with
   granted tools has no path onto it, and no frozen binding exists from prompt-side tool names
   to wire ToolRefs.

From CMA vaults we adopt: write-only secret records addressed by immutable name, injection at
a boundary, rotation for request-time consumers without restart, audit metadata. We reject
egress proxies, placeholder substitution, and OAuth auto-refresh — julep workers run
operator-trusted code, so the vault's job is **distribution + hygiene**, not anti-exfiltration.

## 2. Design summary

| Area | Decision |
| --- | --- |
| Vault | Postgres store (execution store) for **operator/infra credentials**; worker pull; plain-env fallback |
| Reference syntax | Whole-string `secret://<name>` URIs, resolved only at the injection boundary |
| Multi-tenant | **Caller-supplied per-run secrets** — no julep-side tenant storage |
| Surface check | `pin` (canonical definition-hash equality) by default; `names`/`off` escape hatches; alpha knob |
| Retry authority | Never from unasserted MCP hints; explicit assertion or operator policy only |
| In-flight contract | Freeze-time surface assumed for a run's lifetime; no mid-run rechecks |
| dotctx agents | Lower onto the existing **AgentWorkflow** via a frozen alias map; no second loop |

## 3. Vault-lite (operator/infra credentials)

### 3.1 Data model

New numbered migration in the execution store (`projection_sql.py` conventions):

```
secrets(
  name        TEXT PRIMARY KEY,          -- ^[a-z0-9][a-z0-9_-]{0,63}$
  ciphertext  BYTEA,                     -- AES-GCM; NULL when archived
  key_id      TEXT NOT NULL,             -- vault key that encrypted this row
  generation  BIGINT NOT NULL,           -- bumped on every PUT; cache/version token
  created_at  TIMESTAMPTZ NOT NULL,
  updated_at  TIMESTAMPTZ NOT NULL,
  updated_by  TEXT NOT NULL,             -- API key name (audit)
  archived_at TIMESTAMPTZ                -- archive purges ciphertext, keeps the row
)
```

**Dedicated vault key ring:** `JULEP_VAULT_KEYS` / `JULEP_VAULT_KEY_ID`, same wire format as
the `TEMPORAL_PAYLOAD_KEYS` codec but a separate, purpose-derived ring — one key must not
serve two security domains. AAD binds (name, generation) so ciphertext cannot be replayed
across rows or versions. Rotation protocol: old key ids stay decode-available.
`julep db reencrypt-secrets` is a **maintenance-window operation**: it takes an
exclusive transaction lock on the execution-store `runs` and `secrets` tables, refuses to
start while any run is non-terminal, re-encrypts all rows under the active key, and reports
progress. Operators stop new submissions before invoking it. A key may be retired only when
the sweep reports zero rows referencing it. Restoring the DB requires the ring covering every
`key_id` present.

No version history: `PUT` overwrites (generation++); `archive` nulls ciphertext, keeps the
row; `DELETE` removes it.

### 3.2 API surface (`/v1`, bearer) and key roles

| Endpoint | Role | Notes |
| --- | --- | --- |
| `PUT /v1/secrets/{name}` `{ "value": "..." }` | admin | Create/update. **Write-only**: value never echoed. |
| `GET /v1/secrets` | admin | Names + metadata only. Workers get no list endpoint. |
| `GET /v1/secrets/{name}/value` | **worker** | The single read path, gated by the allowlist below. Admin keys cannot read values — break-glass is provisioning a worker-role key deliberately. |
| `POST /v1/secrets/{name}/archive` | admin | Purge ciphertext, keep record. Evicts caches. |
| `DELETE /v1/secrets/{name}` | admin | Hard delete. Evicts caches. |

**Key roles, backward-compatible:** `parse_api_keys` splits entries on commas and whitespace,
so the third segment stays a **single role token**: `name:token[:admin|:worker]`; existing
`:admin` strings parse unchanged; anything else errors. `ApiKey` grows
`role: {client, worker, admin}`; every route gets an explicit dependency (`require_client`,
`require_worker`, `require_admin`) and existing `require_key` routes are audited: a worker key
is rejected everywhere except the value fetch (+ unauthenticated health).

**Worker read scoping:** `[tool.julep.server] worker_secret_allowlist = [...]`
(env `JULEP_WORKER_SECRET_ALLOWLIST`), fail-closed — no allowlist, no worker reads. Values
never appear in server logs; the SSE/projection plane never carries them.

### 3.3 `secret://` resolution

Whole-string references resolve at the **injection boundary**, never at parse or freeze.
Secret-capable surfaces, split by consumer class:

- **Request-time consumers** — `[tool.julep.mcp.servers.*.headers]` values, read per call
  through the shared MCP transport (§4.2). These get rotation-without-restart.
- **Startup-time consumers** — `ServerSettings` secret-typed fields (e.g.
  `temporal_api_key`, read once for the long-lived Temporal connection) and materialized
  worker env. These resolve once at process start; rotation requires restart/reconnect, and
  the docs say so per surface. No blanket 60-second promise.

`SecretResolver` chain (new `julep/secrets.py`):

0. **Run-supplied secrets** (§3.5), by logical name.
1. **Control plane**: `GET /v1/secrets/{name}/value` when `JULEP_API_URL` + a worker-role key
   are configured; per-process cache, 60 s TTL, keyed by (name, generation). Stale-if-error
   is bounded and typed: stale values serve only for transient failures (network, 5xx) and at
   most **15 minutes**, then fail closed; 401/403/404/410, archive, and delete evict
   immediately — revocation wins over availability.
2. **Env fallback**: `JULEP_SECRET_<NAME>` (uppercased, `-`→`_`). The local-dev story, and
   the authoring-time path for freeze-time snapshot fetches.
3. Otherwise **fail closed**, naming the secret and every chain step tried.

**Value scrubbing** (key/path-pattern redaction cannot catch echoed values): operator-vault
and env values register in a process-wide dynamic scrubber holding exact values plus base64
and URL-encoded variants. Caller-supplied run values are instead scrubbed **only in that
run's context**; they never enter a process-global registry where one caller's short value
could redact another run's data or accumulate forever. The applicable scrubber is composed
into trajectory capture, projection egress (pre-`value_ref`), activity-failure serialization,
and MCP/HTTP transport diagnostics; request headers/bodies are never logged by default.
Honest scope: this protects julep-controlled persistence; it cannot stop a remote endpoint
from deliberately echoing a credential into a tool result.

Freezing: references pass through as strings; no resolution output flows into release or
artifact bytes. `julep doctor` gains a dangling-reference check.

### 3.4 Rotation and audit

Request-time consumers pick up rotation within ~TTL without restart; startup-time consumers
on restart/reconnect. Audit: metadata (`updated_by`, `generation`, timestamps, archive
records) + server log lines.

### 3.5 Multi-tenant: caller-supplied run secrets

One flow, one MCP server config, per-tenant credentials — solved by the caller supplying the
credential with the run, which removes any shared tenant storage and with it any
julep-side authorization question: a submitter can only route a credential it already holds.
Julep authenticates submitters; tenant identity belongs to the application.

1. **Submission and inferred bindings**:
   `POST /v1/runs { ..., "secrets": { "<logical-name>": "<value>" } }` — real values over
   TLS, keyed by the same logical names config uses. Config stays tenant-blind:
   `Authorization = "secret://tracker-token"`. There is no second binding declaration: at
   preflight, the worker derives the allowed names from whole-string `secret://` references
   in the resolved request-time config for MCP servers referenced by the frozen release.
   Submitted names outside that set fail the run before user/tool effects. When the control
   plane has the same environment config it may reject them synchronously as a convenience;
   worker preflight remains authoritative. Supplying an allowed name intentionally shadows
   the operator vault/env value of the same name for that run.
   This first version deliberately supports **MCP request-header references only**; it does
   not inject caller-supplied values into LLM/provider credentials or arbitrary worker env.
   Submission is capped at 32 entries, 16 KiB UTF-8 per value, and 64 KiB total (names plus
   values).
2. **Non-persistence contract**: the `secrets` field is stripped at ingest — it never reaches
   the stored run input (`input_ref` / projection values), `GET /v1/runs`, SSE, traces, or
   server logs. Values ride only inside `FlowInput` under the Temporal payload codec
   (AES-GCM); the server **refuses** run secrets when payload encryption is off. On the
   worker, values are supplied to the run-scoped scrubber (§3.3), never the process-global
   registry.
3. **Resolution**: step 0 of the chain, ahead of vault and env.
4. **Carriage**: the map threads `FlowInput` → child `FlowInput`s → `AgentInput` →
   `CallToolInput`, projection/diagnostic activities that may serialize run values, and every
   continue-as-new constructor. Each boundary constructs the scrubber from that run's map.
   Absent field ⇒ none; old histories replay unchanged; command-producing changes are
   patch-gated.
5. **Cache identity**: after a fetch returns its generation, resolver entries use
   `(name, generation)` as their version/freshness token. Transport/preflight caches key on
   server-config digest + ordered
   sink→value-hash mapping + policy — never raw values, no unordered-set collision when two
   secrets swap headers.
6. **Pinning trade-off, documented**: values are fixed for the run's lifetime — no mid-run
   rotation or revocation; revoking a tenant credential means terminating its in-flight runs.
   Right-sized for episodic runs; long-lived runs should prefer operator-vault refs.
7. **Start paths**: run secrets are supported through `/v1/runs` and the Julep CLI start
   helper. The CLI verifies that its Temporal client uses the AES-GCM converter and refuses
   otherwise. Raw/direct Temporal SDK starts must not attach run secrets because the
   workflow cannot determine how its input was encoded. `JULEP_SECRET_*` remains the
   direct/local-development fallback.

## 4. MCP surface contract

### 4.1 Frozen data and retry authority

- `FrozenTool` (and its release serialization) gains **normalized annotations** (MCP defaults
  applied per the negotiated protocol version), the **protocol version**, and **assertion
  provenance**.
- **Retry authority is severed from hints:** `_retry_policy_for` must never authorize more
  than one attempt from an **unasserted** contract. Retries > 1 require `asserted=True`
  (capability manifest / native declaration / explicit operator override). Preflight is
  defense-in-depth, never retry authority.
- The surface check is **`pin`: canonical definition-hash equality per referenced tool**
  (only tools the flow actually calls). Any difference fails closed with a diff-style detail
  payload. `names` (presence only) and `off` are explicit, documented, unsafe escape hatches.
  Structural "compatibility" checking of JSON Schema is not attempted — top-level checks miss
  nested `required`, enum narrowing, bounds, `additionalProperties` flips; a checker that
  passes those is worse than none.

### 4.2 One MCP transport

New `McpTransport` abstraction (in the `julep/mcp_auth.py` orbit): `list_tools()` +
`call_tool()`, built from one place that resolves server URL + headers (+ `secret://` refs)
from worker config — the same transport serves runtime calls, worker preflight, and (via the
CLI) freeze-time snapshots. `mint_token` gains a **discovery scope** (`tools/list`,
deterministic idempotency key `preflight:{workflow_id}:{server}`) so servers can distinguish
discovery from invocation. Endpoint/header config stays worker-side (`[tool.julep.mcp.servers]`),
not release content — releases stay portable across environments.

### 4.3 Enforcement: run-start preflight (worker-side, replay-safe)

A preflight activity runs as the first scheduled activity of any run whose release references
MCP tools:

- Worker-side (the run's network path + signing key); per-worker cache, 30 s TTL, keyed by
  the full transport identity (§3.5.5); transport errors retry under the normal activity
  retry policy.
- Mismatch ⇒ typed `tool_surface_mismatch`: terminal `failed`, machine-readable detail
  (server, tool, frozen vs fresh definition hash, human-readable diff), **zero user/tool
  effects** (framework setup may have run; no reasoner or tool activity has).
- **Refusal is an asynchronous terminal state.** `POST /v1/runs` keeps returning `accepted`;
  the refusal is visible in `GET /v1/runs/{id}`, `GET .../result?wait_s=`, and SSE.
- **Replay discipline:** absent policy field in `FlowInput` ⇒ `off` (old histories replay
  unchanged); the new activity is gated behind `workflow.patched("mcp-preflight")`; the
  effective policy is captured from the release at freeze (`[tool.julep.mcp] preflight`,
  alpha), overridable only by an authorized submission parameter; and
  `preflight = {policy, completed, surface_digest}` rides `FlowInput` across continue-as-new.
- **Run-secret binding is unconditional:** the same first activity always validates submitted
  names against whole-string references on release-referenced servers, including when the
  surface policy is `off`. `off` disables live `tools/list` comparison, not secret routing
  validation.

**Activation-time advisory:** `POST /v1/deployments` runs the same check best-effort from the
control plane when reachable, storing per-server status on the deployment record (schema
addition). Advisory only — the worker preflight is the enforcement point.

### 4.4 Mid-run drift

No rechecks mid-run or across CAN. Call-site drift signatures (tool-not-found; server-side
input-schema rejection) become **`ToolSurfaceDrift`**. Before dispatch, AgentWorkflow validates
model arguments against the frozen `inputSchema`. Failure there is a model/tool-call error and
returns as an observation for another round; only arguments that pass the frozen schema but are
then schema-rejected by the live server prove drift. `ToolSurfaceDrift` is added to the harness's non-retryable
classification and **detected through the `ActivityError` cause chain in AgentWorkflow's tool
dispatch**, projected as a typed failure and **re-raised** — without this, AgentWorkflow
converts tool activity errors into observations for the next model round and the drift signal
is swallowed. Tested on both the sequential and concurrent (READ) dispatch paths. Author
contract: changing a server's interface ⇒ redeploy referencing flows; in-flight runs assume
the frozen surface. Manual snapshots (`deploy(mcp_listings=)`, `--mcp-snapshot`) get the
identical preflight; author-managed means the freedom to set `preflight = "off"` and own it.

## 5. dotctx agents on AgentWorkflow

### 5.1 Binding

```toml
[tool.julep.mcp.servers.tracker]
url = "https://tracker.example.com/mcp"
headers = { Authorization = "secret://tracker-token" }

[tool.julep.pipeline.issue_dedup]
ctx = "prompts/issue_dedup"
lane = "triage"

[tool.julep.pipeline.issue_dedup.tools]
search_similar_posts = "tracker:search-similar-posts"
```

Packages stay mem-mcp-shaped (bare Python-identifier keys; contracts in `tools.pyi`). Freeze:

1. snapshots the bound servers through `mcp_snapshot`;
2. resolves every bare key through the pipeline's `tools` map — unbound key, unknown
   server/tool ⇒ loud freeze error;
3. validates `tools.pyi` stubs against the frozen `inputSchema` by canonical-schema
   equality through `ToolSchemaExpectation`. The authoring check directionally tolerates
   only extra `additionalProperties: false` keywords emitted by signature-derived served
   schemas, because `tools.pyi` cannot express that marker; an expectation that explicitly
   closes an object still drifts from an open served schema. Runtime surface pins remain
   byte-exact;
4. records the **alias map** bare-key → wire `ToolRef` in the release. The model-visible tool
   name is the bare key, mapped to the MCP wire name at dispatch.

Retargeting a package to another server — or to fakes in eval — never touches the package.

### 5.2 Execution

`reasoner_to_flow` lowers a tool-bearing reasoner to the **`app` shape running
`AgentWorkflow`** — bounded by `max_rounds` when set, by `[tool.julep] agent_round_cap`
(default 32) for `agent: true`. Reasoners without tools retain their current lowering and
byte-identical release hashes.

`AgentInput` is extended with the frozen alias map, tool definitions (schemas presented to
the provider under bare names), and contracts. Inherited from AgentWorkflow: deterministic
activity cids (the `mcp_auth` `idk` binding), READ-concurrent / write-serialized dispatch,
`require_tool_call`, the budget guard, and the mid-loop continue-as-new seam.

The lowering also requires:

- **Real output validation**: final answers validate against the reply schema with an actual
  JSON-Schema validator, re-prompting within `output_retries`.
- **Durable canonical transcript**: tool-call ids, names, arguments, result refs, and
  ordering persist and ride across CAN independently of prompt-context truncation.

### 5.3 Declarations blob

The declarations blob uses schema version 2 and carries reasoners, renderers, alias maps,
frozen tool definitions/contracts, and tool grants. Hydration is **release-scoped** (keyed by
declarations hash) so two releases defining the same logical reasoner differently coexist on
one worker; hydration happens before `resolveAgentSpec`, which receives a declarations ref.
Generic workers (no `WORKER_APPLICATION`) run zero-code agents from the release alone.

### 5.4 Local/eval story

`dry_run`/`adry_run`/`julep eval` accept `tools={bare_key: callable}` fakes through the
`mcp_call` seam; `julep run <path>.ctx` works keyless with fakes and live with config-bound
servers. `examples/dotctx/issue_dedup` upgrades from declarative to actually running.

## 6. Error handling summary

| Condition | Classification | Surfaced |
| --- | --- | --- |
| Referenced tool hash mismatch / missing at run start | `tool_surface_mismatch` (terminal; zero user/tool effects) | async terminal state: runs API, result?wait_s, SSE |
| Drift signature mid-run | `ToolSurfaceDrift`, non-retryable, re-raised out of the agent loop | run failure + typed projection event |
| Round budget exhausted | `round_budget_exhausted` (existing AgentWorkflow semantics) | run failure + transcript |
| `require_tool_call` violated | typed failure (existing) | run failure + transcript |
| Final output fails schema after `output_retries` | typed validation failure | run failure + transcript |
| `secret://` unresolvable / revoked | fail-closed error naming secret + chain | startup or call site |
| Submitted run-secret name is unused by resolved config for the release-referenced MCP servers | `invalid_run_secret_binding` (terminal; zero user/tool effects) | synchronous 400 when known, otherwise async terminal state |
| Run `secrets` submitted while payload encryption is off | 400 at submission | `POST /v1/runs` |
| Vault transient outage, cached value | stale served ≤ 15 min, then fail closed | worker logs |
| Non-worker key reads a value; worker key off-allowlist or on non-secret routes | 403 | API |
| Freeze: unbound key / unknown tool / stub-schema mismatch | freeze error | `julep plan/apply` / `deploy()` |

## 7. Testing

- **Retry authority**: unasserted contract never yields attempts > 1 regardless of hints;
  asserted paths unchanged.
- **Pin check**: hash-equality matrix (identical ⇒ pass; any schema/annotation/name change ⇒
  typed mismatch with diff); normalized-annotation persistence round-trips through release
  JSON; `names`/`off` honored.
- **Preflight**: fixture MCP server mutated between freeze and run ⇒ refused asynchronously
  with detail; `workflow.patched` gating replays old histories cleanly; policy + completed +
  digest across CAN; cache TTL; transport-error retries.
- **Transport**: one transport serves call/list/snapshot; discovery-scope tokens verified;
  header `secret://` resolution per call.
- **Run secrets**: inferred allowed-name set from only the release-referenced MCP servers;
  unknown-name refusal before user/tool effects; intentional shadowing of same-name vault/env
  values; non-persistence (stored `input_ref`, `GET /v1/runs`, SSE, projection values never
  contain submitted values — asserted against the raw store); submission refused without
  payload encryption; step-0 precedence; threading through child flows, AgentInput,
  CallToolInput, projection/diagnostic activities, and both CAN paths; value-hash cache
  identity (header-swap collision); isolation between concurrent run-scoped scrubbers; CLI
  refusal without the AES-GCM converter; raw/direct Temporal starts documented unsupported.
- **Vault**: role parsing back-compat; route audit (worker key 403 everywhere but value
  fetch); allowlist fail-closed; AAD binding (row/generation swap fails to decrypt); key-ring
  rotation + maintenance-only `reencrypt-secrets` (active-run refusal, exclusive table lock,
  retirement guard); resolver chain, TTL, bounded stale-if-error, immediate revocation
  eviction; scrubber catches exact/base64/urlencoded echoes at all four boundaries.
- **Agent lowering**: tool-bearing reasoner ⇒ app/AgentWorkflow with alias map (goldens);
  non-tool reasoners byte-identical; alias-mapped dispatch; READ-concurrent determinism;
  frozen-input validation keeps bad model arguments as observations; live schema rejection
  after frozen validation plus tool-not-found become `ToolSurfaceDrift`, re-raised on sequential
  and concurrent paths; JSON-Schema output
  validation + `output_retries`; canonical transcript across CAN.
- **Declarations blob**: schema-version-2 golden; release-scoped hydration (two conflicting
  releases coexist); generic worker runs the issue-dedup agent from the release alone.
- **Live**: issue-dedup agent, vault-referenced header, submitted through `/v1/runs` with a
  run secret, SSE to terminal; then a drift injection (tools server restarted with a changed
  schema) ⇒ typed refusal.

## 8. Sequencing

- **PR-B0 (first, small):** retry-authority fix (unasserted contracts cap at 1 attempt) +
  normalized-annotation persistence in `FrozenTool`/releases.
- **PR-A: vault-lite** — migration, `/v1/secrets`, key roles + route audit, allowlist,
  `julep/secrets.py` resolver + scrubber, run-secrets ingest at `POST /v1/runs`
  (strip-before-store, encryption-required; reject as unsupported until PR-B is deployed),
  vault key ring + maintenance-only
  `db reencrypt-secrets`, doctor check, docs.
- **PR-B: surface contract** — `McpTransport` + discovery scope, `pin` check, preflight
  behind `workflow.patched`, policy pinning + CAN carriage, authoritative inferred run-secret
  binding validation, run-secret threading (FlowInput/AgentInput/CallToolInput/child starts/
  projection diagnostics/CAN) + identity-complete cache keys, drift classification +
  AgentWorkflow re-raise, activation advisory, docs.
- **PR-C: dotctx agents** — binding config + freeze validation + alias map, lowering to
  app/AgentWorkflow, `AgentInput` extension, output validation + canonical transcript,
  declarations blob schema 2 + release-scoped hydration, eval fakes, issue-dedup example
  upgrade, docs. Depends on B0/B; consumes A.

## 9. Out of scope

Directional JSON-Schema compat mode; OAuth auto-refresh; egress proxies/placeholders;
julep-side tenant secret storage; per-secret host binding; secret version history + webhooks;
LISTEN/NOTIFY rotation push; MCP *server* authoring; sourcing `worker_secret_environment`
(K8s) from the vault; caller-supplied run secrets for LLM/provider credentials or arbitrary
worker environment variables.
