# RFC: Secret vault (lite), MCP surface contract, and the dotctx tool loop

- **Status:** draft (initial RFC for independent review)
- **Owner:** Diwank Singh Tomer
- **Date:** 2026-07-22
- **Reviewers:** codex `gpt-5.6-sol` @ high (independent design review)
- **Depends on:** the `julep3-post-port` program (control plane `/v1`, schema-v2 releases with
  `runtimeDeclarationsRef`, `mcp_tool()` + snapshot-at-freeze, `julep.mcp_auth`, redaction wiring)

## 1. Motivation

Two gaps surfaced by the mem-mcp port and the CMA credential-vault research:

1. **Secrets are literal strings.** MCP server auth headers live verbatim in
   `[tool.julep.mcp.servers.*.headers]`; provider keys arrive as ambient worker env; the only
   managed path is Helm's `worker_secret_environment` → K8s `secretKeyRef` (K8s-only, restart to
   rotate, no local-dev story). Nothing stops a secret from being committed to config or drifting
   into logs.
2. **The frozen MCP tool surface is unenforced.** Freezing snapshots `tools/list` and derives
   retry/effect contracts from `McpAnnotations`, but nothing checks that the *live* server still
   honors that surface at run time. Drift (removed tool, new required field, an
   idempotency-annotation downgrade) currently surfaces as an opaque mid-run activity failure —
   or worse, as a retry policy that is no longer safe.

Relatedly, dotctx packages declare `tools:` keys that are **declarative only**; agent-shaped
packages (`max_rounds`, `agent: true`) cannot run zero-code because julep has no tool-calling
loop of its own (`agent: true` lowers to `app()`, which expects an application-side controller).

### What we take from CMA vaults — and what we deliberately do not

Adopted: write-only secret records addressed by immutable name; injection at a boundary;
rotation propagating to running workers without restart; values never readable back through the
write path; audit metadata.

Rejected (trust model differs): CMA substitutes placeholders at an egress proxy because its
sandbox runs untrusted model-driven code. Julep workers run **operator-trusted code**; the
model-visible surface is reasoner context, and the projection already has fail-closed
secret-shaped redaction. So: no egress proxy, no placeholder strings, no OAuth auto-refresh.
The vault's job here is **distribution + hygiene**: central storage, reference-by-name from
config, injection at the worker/server boundary, zero secret material in git, releases,
artifacts, projection, or logs.

## 2. Decisions already locked with the owner

| Decision | Choice |
| --- | --- |
| Spec shape | One coupled spec (vault + MCP surface + dotctx loop) |
| Vault threat model | Distribution + hygiene (trusted workers; no egress proxy) |
| Vault plumbing | Postgres store in the execution store + worker **pull**; plain-env fallback |
| Reference syntax | Whole-string `secret://<name>` URIs |
| dotctx tool binding | Binding-free packages: bare keys + `[tool.julep.pipeline.<name>.tools]` map |
| Surface check default | `compat` (structural compatibility, not names-only) |
| Preflight exposure | Alpha-namespaced config knob; semantics may tighten |
| In-flight contract | Julep assumes freeze-time surface holds for a run's lifetime; no mid-run rechecks |
| Loop scope v1 | One julep-owned loop: bounded (`max_rounds`) + capped open-ended (`agent: true`) |

## 3. Vault-lite

### 3.1 Data model

New numbered migration in the execution store (`projection_sql.py` conventions):

```
secrets(
  name        TEXT PRIMARY KEY,          -- ^[a-z0-9][a-z0-9_-]{0,63}$
  ciphertext  BYTEA,                     -- AES-GCM over the UTF-8 value; NULL when archived
  key_id      TEXT NOT NULL,             -- which payload key encrypted it
  created_at  TIMESTAMPTZ NOT NULL,
  updated_at  TIMESTAMPTZ NOT NULL,
  updated_by  TEXT NOT NULL,             -- API key name (audit)
  archived_at TIMESTAMPTZ                -- archive purges ciphertext, keeps the row
)
```

Values are encrypted with the **existing** AES-GCM payload keys (`JULEP_PAYLOAD_KEYS`,
`payload_key_id` selects; no new key infrastructure). No version history in v1: `PUT` overwrites;
`archive` nulls the ciphertext and keeps the row for audit; `DELETE` removes the row.

### 3.2 API surface (`/v1`, bearer)

| Endpoint | Role | Notes |
| --- | --- | --- |
| `PUT /v1/secrets/{name}` `{ "value": "..." }` | admin | Create/update. **Write-only**: value never echoed; response is metadata. |
| `GET /v1/secrets` | admin, worker | Names + metadata (timestamps, updated_by, archived). Never values. |
| `GET /v1/secrets/{name}/value` | **worker only** | The single read path. Admin keys are write-only by design (humans should not casually read secrets back; workers are the injection boundary). |
| `POST /v1/secrets/{name}/archive` | admin | Purge ciphertext, keep record. |
| `DELETE /v1/secrets/{name}` | admin | Hard delete. |

**API-key roles:** `JULEP_API_KEYS` entries grow from `name:token[:admin]` to
`name:token[:flag,...]` with flags ⊆ `{admin, worker}`. Existing `:admin` strings parse
unchanged. `worker` grants exactly: `GET /v1/secrets`, `GET /v1/secrets/{name}/value`. A worker
key is NOT an admin key and cannot submit runs (default client role is a third, implicit state).
Values never appear in server logs; the SSE/projection plane never carries them.

### 3.3 `secret://` resolution

Whole-string references: a secret-capable config value equal to `secret://<name>` resolves at
the **injection boundary**, never at parse or freeze. v1 secret-capable surfaces:

- `[tool.julep.mcp.servers.*.headers]` values (both freeze-time snapshot fetch and runtime
  `http_mcp_caller` transport headers),
- `ServerSettings` secret-typed fields (e.g. `temporal_api_key`),
- worker env injection values in `[tool.julep.server] worker_environment` (letting the Helm
  path source from the vault instead of pre-created K8s secrets is a v2 extension; v1 keeps
  `worker_secret_environment` as-is).

`SecretResolver` chain (new `julep/secrets.py`):

1. **Control plane**: when `JULEP_API_URL` + a worker-role key are configured — `GET
   /v1/secrets/{name}/value`, cached per-process with a 60 s TTL. On refresh failure with a
   cached value present: keep serving the stale value and warn (rotation lag beats an outage);
   fail only when no value was ever fetched.
2. **Env fallback**: `JULEP_SECRET_<NAME>` (name uppercased, `-`→`_`). This is the whole
   local-dev story: no control plane needed.
3. Otherwise **fail closed** with an error naming the secret and both chain steps tried.

Resolved values are registered as exact-match patterns with the worker's redactor
(`build_redactor` composition), so an accidental echo into the projection is scrubbed.

Freezing: references pass through as strings; snapshot listings never contain header values; by
construction no resolution output flows into release/artifact bytes. `julep doctor` gains a
check for dangling `secret://` references (config names not resolvable by the chain).

### 3.4 Rotation and audit

`PUT` + TTL expiry ⇒ running workers pick up a rotated value within ~60 s, no restart — the
CMA property that motivated worker-pull. Audit in v1 is metadata only (`updated_by`,
timestamps, archive records) plus server log lines; webhooks/history are out of scope.

## 4. MCP surface contract

### 4.1 Compatibility check (`julep/mcp_surface.py`)

`check_referenced_surface(frozen_referenced_tools, fresh_listing) -> list[Incompatibility]`,
where the frozen side is only the tools the flow actually calls. Incompatibility classes:

- **(a) missing** — referenced tool absent from the fresh listing;
- **(b) new required input** — fresh `inputSchema.required` contains a property the frozen
  schema did not require (frozen-era calls would start failing validation);
- **(c) declared property removed/retyped** — a property the frozen schema declared is gone or
  changed JSON type;
- **(d) annotation safety downgrade** — `idempotentHint` true→false/absent, `readOnlyHint`
  true→false, `destructiveHint` false/absent→true. This is the highest-severity class: frozen
  retry/effect contracts were derived from those annotations, so a downgrade silently makes
  retries/replays unsafe.

Additive/benign changes (new tools, new optional inputs, description text) pass. This is a
decidable structural check; full JSON-Schema subsumption is deliberately not attempted.

### 4.2 Enforcement: run-start preflight (worker-side)

A **preflight activity** runs as the first step of any run whose release references MCP tools:

- Executes on the worker (the only place with the run's network path AND
  `JULEP_MCP_SIGNING_KEY` to make the same authenticated `tools/list` the run will make).
- Per-worker cache, 30 s TTL, so hot pipelines don't pay a listing per run.
- Transport errors retry under the normal activity retry policy (a server that is down would
  fail the first tool call anyway).
- Any incompatibility ⇒ the run terminates with typed `tool_surface_mismatch`: terminal
  `failed`, machine-readable detail (server, tool, incompatibility class, frozen vs fresh
  fragment), **zero effects executed**. The control plane surfaces this as the run-refused
  answer to `POST /v1/runs` consumers.

**Policy knob (alpha surface):** `[tool.julep.mcp] preflight = "compat" (default) | "names" |
"off"`. The chosen policy is pinned into `FlowInput` at submission so replays and
continue-as-new segments see a stable decision. Marked alpha in docs: semantics may tighten
without a deprecation window.

**Activation-time advisory:** `POST /v1/deployments` runs the same check best-effort from the
control plane when the servers are reachable from there, recording per-server compat status on
the deployment record (`GET /v1/deployments` shows it). Advisory only — the worker preflight is
the enforcement point.

### 4.3 Mid-run drift

No rechecks mid-run or across continue-as-new. Call-site failures that match drift signatures
(tool-not-found; server-side input-schema rejection) are classified as **non-retryable**
`ToolSurfaceDrift` application errors with a projection event naming what moved. The documented
author contract: changing a server's interface ⇒ redeploy referencing flows; in-flight runs are
assumed to run against the freeze-time surface, and drift mid-run is an explicit, typed failure
— not a retry loop.

Manual/author-managed snapshots (`deploy(mcp_listings=)`, `--mcp-snapshot` fixtures) get the
identical preflight; the author-responsibility tier is the same mechanism plus the freedom to
set `preflight = "off"` and own the consequences.

## 5. dotctx MCP tools and the julep-owned loop

### 5.1 Binding (Option 1: binding-free packages)

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

The `.ctx` package stays exactly mem-mcp-shaped: bare Python-identifier keys in
`settings.yaml tools:` and contracts in `tools.pyi`. Freeze:

1. snapshots the bound servers (existing `mcp_snapshot`),
2. resolves every bare key through the pipeline's `tools` map — unbound key, unknown
   server/tool ⇒ loud freeze error,
3. validates the `tools.pyi` contract against the frozen `inputSchema` (decidable
   approximation: contract parameter names ⊆ schema properties; contract required parameters
   match schema `required`) — mismatch ⇒ loud freeze error,
4. records key→(server, tool, contract) in the frozen release; the **model-visible tool name is
   the bare key** (Pythonic, matches the prompt text), mapped to the MCP wire name at dispatch.

Retargeting a package to another server — or to fakes in eval — never touches the package.

### 5.2 Loop semantics

New execution shape `tool_loop(reasoner, bound)` produced by `reasoner_to_flow` when a reasoner
has granted tools:

- `max_rounds: N` ⇒ bound N; `agent: true` ⇒ bound `[tool.julep] agent_round_cap` (default
  32). Reasoners without tools lower exactly as today (hash stability: existing releases are
  unaffected; the new node only appears when tools are granted).
- Each round: `invokeReasoner` activity with provider-native tool definitions (bare key names,
  frozen `inputSchema`s) → the model returns either tool calls or a final answer.
- Tool calls execute as the existing MCP call activities (deterministic `cid` per call — the
  same identity that `mcp_auth` binds into the `idk` claim). v1 executes a round's calls
  **sequentially** in declared order for determinism simplicity; parallel rounds are v2.
- Results append to the transcript (`__julep_meta__` machinery); loop until a final answer or
  the bound is exhausted ⇒ typed `round_budget_exhausted` failure.
- `require_tool_call: true` ⇒ a final answer with zero tool calls made is rejected as a typed
  failure (round 1 must call a tool).
- The final answer validates against the reply schema with existing `output_retries` semantics.
- The tool grants + bindings ride the schema-v2 declarations blob, so generic workers (no
  `WORKER_APPLICATION`) reconstruct the loop config from the release alone.

### 5.3 Local/eval story

`dry_run`/`adry_run`/`julep eval` accept `tools={bare_key: callable}` fakes through the existing
`mcp_call` seam; `julep run <path>.ctx` works keyless with fakes and live with config-bound
servers. The `examples/dotctx/issue_dedup` package (landing separately) upgrades from
"declarative tools" to an actually-running loop when this ships.

## 6. Error handling summary

| Condition | Classification | Surfaced |
| --- | --- | --- |
| Referenced tool missing / schema incompatible at run start | `tool_surface_mismatch` (terminal, zero effects) | run status + detail; SSE terminal event |
| Drift signature mid-run | `ToolSurfaceDrift`, non-retryable | run failure + projection event |
| Round budget exhausted | `round_budget_exhausted` | run failure + transcript |
| `require_tool_call` violated | typed failure | run failure + transcript |
| `secret://` unresolvable | fail-closed error naming secret + chain | worker/server startup or call site |
| Vault unreachable, cached value present | stale value served + warning | worker logs |
| Non-worker key reads a value | 403 | API |
| Freeze: unbound key / unknown tool / contract mismatch | freeze error | `julep plan/apply` / `deploy()` |

## 7. Testing

- **Compat matrix** (unit): each incompatibility class + additive-change passes; annotation
  downgrade permutations.
- **Preflight E2E**: fixture MCP server mutated between freeze and run (remove tool, add
  required field, retype, downgrade annotation) ⇒ refused with the right class; `names`/`off`
  policies honored; policy pinned across continue-as-new.
- **Vault**: role enforcement (admin write-only, worker read, client 403s); write-only responses;
  encryption round-trip + key_id selection; resolver chain (control plane → env → fail-closed),
  TTL refresh, stale-if-error; redactor registration; doctor dangling-ref check.
- **Loop**: goldens for lowering (tools ⇒ `tool_loop`, bound resolution); round accounting;
  sequential call order determinism; recorded-history replay across rounds; CAN mid-loop;
  `require_tool_call`; reply-schema retry; `ToolSurfaceDrift` classification.
- **Freeze binding**: unbound/unknown/mismatch errors; golden release with key→(server, tool)
  map; generic-worker rehydration from the declarations blob.
- **Live**: issue-dedup agent against the sample tools server with a vault-referenced header,
  submitted through `/v1/runs`, consumed over SSE.

## 8. Sequencing

- **PR-A: vault-lite** — migration, `/v1/secrets`, key roles, `julep/secrets.py` resolver,
  redactor registration, doctor check, docs. Independent.
- **PR-B: MCP surface contract** — `mcp_surface.py`, preflight activity + policy knob (alpha),
  drift classification, activation advisory, docs. Independent of A.
- **PR-C: dotctx binding + tool loop** — binding config + freeze validation, `tool_loop`
  execution shape, declarations-blob carriage, eval fakes, upgrade the issue-dedup example,
  docs. Depends on B; consumes A for headers.

## 9. Out of scope (v1)

OAuth auto-refresh; egress proxies/placeholder substitution; per-secret host/server binding;
secret version history + webhooks; LISTEN/NOTIFY rotation push (TTL polling suffices); parallel
tool-call execution within a round; MCP *server* authoring (application-side by design);
sourcing `worker_secret_environment` (K8s) from the vault.

## 10. Open questions for review

1. Stale-if-error grace: unbounded (serve stale until restart) or capped (e.g. 15 min, then
   fail closed)?
2. Should admin keys really be barred from `GET .../value`, or is write-only-for-admins
   security theater given admins can mint worker keys?
3. Preflight policy pinned in `FlowInput` at submit — right call, or should re-runs of old
   releases pick up the *current* config default?
4. Sequential-only tool calls per round: acceptable v1 constraint, or does any target workload
   need parallel rounds immediately?
5. Annotation-downgrade class (d): should `destructiveHint` absent→true count (absent is
   conservative-unknown in MCP semantics)?
