# RFC: Secret vault (lite), MCP surface contract, and dotctx agents on AgentWorkflow

- **Status:** v2 — revised after independent review (verdict on v1: needs-rework; S4 unsound,
  S5 reframed). Review log in §11.
- **Owner:** Diwank Singh Tomer
- **Date:** 2026-07-22
- **Reviewers:** codex `gpt-5.6-sol` @ high (adversarial, code-grounded)
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
   conservative contracts from `McpAnnotations`, but nothing checks that the *live* server still
   matches that surface at run time — drift surfaces as an opaque mid-run activity failure.
   Worse (pre-existing bug, confirmed in review): `_retry_policy_for`
   (`harness.py`) chooses retry counts from the tool contract **without checking
   `FrozenTool.asserted`** — an MCP server can claim `idempotentHint: true` and obtain retries
   it is not entitled to. MCP annotations are untrusted hints by spec.

Relatedly, dotctx packages declare `tools:` keys that are **declarative only**. The v1 draft
wrongly claimed julep lacks a tool loop — it does not: `AgentWorkflow`
(`julep/agent_loop.py`, `execution/harness.py:2132+`) is a durable, bounded, native
tool-calling loop with deterministic activity cids, contract-aware dispatch (READ calls
concurrent, writes serialized), `require_tool_call`, and mid-loop continue-as-new. The real gap
is **zero-code wiring**: dotctx reasoners with tools cannot reach AgentWorkflow without
application code, and there is no frozen binding from prompt-side tool names to wire ToolRefs.

### What we take from CMA vaults — and what we deliberately do not

Adopted: write-only secret records addressed by immutable name; injection at a boundary;
rotation for request-time consumers without restart; values never readable back through the
write path; audit metadata. Rejected (trust model differs — julep workers run operator-trusted
code, not model-driven sandboxes): egress proxies, placeholder substitution, OAuth
auto-refresh. The vault's job: **distribution + hygiene** — central storage,
reference-by-name, injection at the worker/server boundary, no secret material in git,
releases, artifacts, projection, or julep-controlled logs.

## 2. Decisions locked with the owner

| Decision | Choice |
| --- | --- |
| Spec shape | One coupled spec (vault + MCP surface + dotctx agents) |
| Vault threat model | Distribution + hygiene (trusted workers; no egress proxy) |
| Vault plumbing | Postgres store in the execution store + worker **pull**; plain-env fallback |
| Reference syntax | Whole-string `secret://<name>` URIs |
| dotctx tool binding | Binding-free packages: bare keys + `[tool.julep.pipeline.<name>.tools]` map |
| Surface check default | **`pin`** (canonical definition-hash equality; see §4.1 — v1 `compat` was unsound) |
| Preflight exposure | Alpha-namespaced config knob; semantics may tighten |
| In-flight contract | Freeze-time surface assumed for a run's lifetime; no mid-run rechecks |
| Loop | **Reuse AgentWorkflow** (review finding 6); no second loop implementation |
| Multi-tenant | **Caller-supplied per-run secrets** (§3.5); the vault stores operator/infra credentials only |

## 3. Vault-lite

### 3.1 Data model

New numbered migration in the execution store (`projection_sql.py` conventions; migrations
currently end at version 8 — this is version 9+):

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

**Dedicated vault key ring** (review finding 12): `JULEP_VAULT_KEYS` / `JULEP_VAULT_KEY_ID`,
same wire format as the existing `TEMPORAL_PAYLOAD_KEYS` codec but a separate, purpose-derived
key ring — reusing the Temporal payload keys would couple two security domains. Encryption
binds AAD = (name, generation), so ciphertext cannot be replayed across rows or versions.
Key rotation protocol: old key ids stay decode-available; `julep db reencrypt-secrets`
re-encrypts all rows under the active key and reports progress; a key may be retired only when
the sweep reports zero rows referencing it. Backup/restore requirement documented: restoring
the DB requires the key ring that covers every `key_id` present.

No version history in v1: `PUT` overwrites (generation++); `archive` nulls ciphertext, keeps
the row; `DELETE` removes it.

### 3.2 API surface (`/v1`, bearer) and key roles

| Endpoint | Role | Notes |
| --- | --- | --- |
| `PUT /v1/secrets/{name}` `{ "value": "..." }` | admin | Create/update. **Write-only**: value never echoed. |
| `GET /v1/secrets` | admin | Names + metadata only (timestamps, updated_by, generation, archived). Workers do NOT get list access (finding 4). |
| `GET /v1/secrets/{name}/value` | **worker** | The single read path, gated by the server-side allowlist below. Admin keys cannot read values (see §10 Q2). |
| `POST /v1/secrets/{name}/archive` | admin | Purge ciphertext, keep record. Evicts caches (§3.3). |
| `DELETE /v1/secrets/{name}` | admin | Hard delete. Evicts caches. |

**API-key roles, backward-compatible** (finding 4): `parse_api_keys` splits entries on commas
AND whitespace, so comma-separated flag lists are unparseable. Instead the third segment stays
a **single role token**: `name:token[:admin|:worker]`; existing `:admin` strings parse
unchanged; anything else in the third position is an error. `ApiKey` grows
`role: {client, worker, admin}`. Every route gets an explicit authorization dependency
(`require_client`, `require_worker`, `require_admin`) and the existing `require_key` routes are
audited in PR-A: a worker key is **rejected** on run submission, run queries, SSE, releases,
deployments, and artifact upload — it can call exactly `GET /v1/secrets/{name}/value` and
`/health`/`/ready`.

**Worker read scoping** (finding 4): a global-read worker key is a skeleton key. v1 adds
`[tool.julep.server] worker_secret_allowlist = ["tracker-token", ...]` (env
`JULEP_WORKER_SECRET_ALLOWLIST`) — fail-closed: with no allowlist configured, worker reads are
denied. Values never appear in server logs; the SSE/projection plane never carries them.

### 3.3 `secret://` resolution

Whole-string references resolve at the **injection boundary**, never at parse or freeze. v1
secret-capable surfaces, split by consumer class (finding 5):

- **Request-time consumers** — `[tool.julep.mcp.servers.*.headers]` values, read per call
  through the shared MCP transport (§4.2). These get the rotation-without-restart property.
- **Startup-time consumers** — `ServerSettings` secret-typed fields (e.g.
  `temporal_api_key`, read once to build the long-lived Temporal connection) and materialized
  worker env. These resolve **once at process start**; rotation requires
  restart/reconnect, and the docs say so explicitly. No false 60-second promise.

`SecretResolver` chain (new `julep/secrets.py`):

1. **Control plane**: `GET /v1/secrets/{name}/value` when `JULEP_API_URL` + a worker-role key
   are configured. Per-process cache with 60 s TTL keyed by (name, generation).
   **Stale-if-error is bounded and typed** (finding 5, §10 Q1): stale values are served only
   for *transient* failures (network, 5xx) and for at most **15 minutes**, then fail closed.
   401/403/404/410, `archived`, and `deleted` evict the cache entry immediately and fail
   closed — revocation must win over availability.
2. **Env fallback**: `JULEP_SECRET_<NAME>` (uppercased, `-`→`_`). The local-dev story; also the
   normal authoring-time path for freeze-time snapshot fetches (admin keys cannot read values,
   so `julep plan/apply` resolves via env or a deliberately-granted worker key).
3. Otherwise **fail closed**, naming the secret and both chain steps tried.

**Secret-value scrubbing** (finding 11 — key/path-pattern redaction cannot catch echoed
values): resolved values register in a process-wide **dynamic value scrubber** holding exact
values plus base64 and URL-encoded variants. The scrubber composes into: trajectory capture,
projection egress (pre-`value_ref`), activity-failure serialization, and MCP/HTTP transport
diagnostics; request headers/bodies are never logged by default. Scope honestly documented:
this protects **julep-controlled persistence**; it cannot stop a remote endpoint from
deliberately echoing a credential into a tool *result* the model then sees.

Freezing: references pass through as strings; no resolution output flows into release or
artifact bytes. `julep doctor` gains a dangling-`secret://`-reference check.

### 3.4 Rotation and audit

Request-time consumers pick up a rotated value within ~TTL (60 s) without restart;
startup-time consumers on restart/reconnect (documented per surface). Audit v1: metadata
(`updated_by`, `generation`, timestamps, archive records) + server log lines. Webhooks,
history, per-secret host binding: out of scope.

### 3.5 Multi-tenant: caller-supplied run secrets (v3 — simplified after second review)

The common case: one flow, one MCP server config, but tenant A's run must call the tracker
with tenant A's credential. Two julep-side-storage designs were drafted and rejected. v2.1
(a free-form `secretBindings: {logical → concrete}` map at submission) was reviewed
(`sol@medium`) and judged **unsound**: the owner check would validate *self-asserted*
identity (keys own only `principal.key`; `merge_principal` accepts caller-supplied `tenant`),
name-level indirection is a credential-routing confused deputy (a bindable global secret
could be pointed at any endpoint whose config shares the logical name), names are not stable
authorization identities across a days-long durable run, allowlist globs are not tenant
isolation, and direct Temporal starts could forge the map. v2.2 fixed all of that with
authenticated key claims, signed run grants, immutable `secret_id`/owner/audience, and
resolution-time revalidation — at the cost of a small authorization system.

**v3 (owner decision) dissolves the problem instead: the caller supplies the credential with
the run.** Every reviewed vulnerability existed because julep held a *shared pool* of tenant
secrets and had to adjudicate which run may touch which entry. When the submitter hands over
the credential, there is no adjudication: you can only "route" a credential you already
possess. This matches julep's trust model — julep authenticates submitters (bearer keys);
tenant identity belongs to the application.

1. **Submission**: `POST /v1/runs { ..., "secrets": { "<logical-name>": "<value>" } }` —
   real values, carried over TLS, keyed by the same logical names config already uses.
   Config stays tenant-blind: `Authorization = "secret://tracker-token"`.
2. **Non-persistence contract**: the `secrets` field is stripped at ingest — it never reaches
   the stored run input (`input_ref` / projection values), `GET /v1/runs`, SSE, traces, or
   server logs. Values ride only inside `FlowInput` under the Temporal payload codec
   (AES-GCM; `require_payload_encryption=True` stands, and this feature *requires* it — the
   server refuses run secrets when payload encryption is off). On the worker, values register
   with the value scrubber (§3.3).
3. **Resolution**: the resolver chain gains step 0 — run-supplied secrets by logical name →
   vault (§3.3) → env → fail closed. The operator vault (§3.1–3.4) remains for
   *infrastructure* credentials; tenant credentials never enter it.
4. **Carriage**: the run-secret map threads `FlowInput` → child `FlowInput`s → `AgentInput` →
   `CallToolInput` → every continue-as-new constructor. Absent field ⇒ none; old histories
   replay unchanged; command-producing changes are patch-gated. (This threading is required
   by any multi-tenant design — it is not overhead specific to this one.)
5. **Cache identity**: transport/preflight caches key on server-config digest + ordered
   sink→value-hash mapping + policy — never raw values, and no unordered-set collision when
   two secrets swap headers.
6. **Pinning trade-off, documented**: values are fixed for the run's lifetime. No mid-run
   rotation or revocation — revoking a tenant credential means terminating its in-flight
   runs. Right-sized for episodic runs; month-long runs should prefer operator-vault refs.
7. **Direct/CLI starts**: the caller constructs `FlowInput` locally and may attach run
   secrets the same way (they are the caller); `JULEP_SECRET_*` env fallback also works.

Deferred indefinitely: julep-side tenant secret storage (owners, audiences, signed grants,
principal-templated references, release-declared binding slots) — revisit only if a caller
genuinely cannot hold credential custody.

## 4. MCP surface contract

### 4.1 What freeze must persist, and retry authority (findings 1, 2)

Two review corrections reshape this section:

- **Annotations are untrusted hints** (MCP spec: effective defaults `readOnlyHint=false`,
  `destructiveHint=true`, `idempotentHint=false`) and today they are **not serialized** in
  `FrozenTool` — only their contribution to `definition_hash` survives. Any annotation-aware
  check needs data that releases do not currently carry.
- **Structural JSON-Schema "compat" checking is unsound**: top-level checks miss nested
  `required`, enum/const narrowing, bounds, `additionalProperties` flips, `oneOf` changes.
  A checker that calls those "compatible" is worse than none.

Therefore:

1. `FrozenTool` (and its release serialization) gains **normalized annotations** (defaults
   applied per the negotiated protocol version), the **protocol version**, and **assertion
   provenance**. Needed for diagnostics and any future conservative compat mode.
2. **Retry authority is severed from hints** — and this lands as the *first commit* of PR-B
   because it fixes a live bug: `_retry_policy_for` must never authorize more than one attempt
   from an **unasserted** contract. Retries > 1 require `asserted=True` (capability manifest /
   native declaration / explicit operator override). Live preflight is defense-in-depth, never
   the source of retry authority.
3. The v1 surface check is **`pin`: canonical definition-hash equality per referenced tool**
   (the hash already covers name, schema, and normalized annotations). Any difference —
   including changes a human would call benign — fails closed with a diff-style detail
   payload. `names` (presence only) and `off` are explicit, documented, unsafe escape hatches.
   A directional, provably-conservative `compat` mode (accept a change only when every input
   admitted by the frozen schema is admitted by the fresh one; unclassifiable ⇒ fail) is
   future work behind the same alpha knob.

### 4.2 One MCP transport, shared by calls, snapshots, and preflight (finding 3)

Today snapshot discovery is author-side (`cli/application.py`, `deploy.py`) and
`http_mcp_caller` implements only `call_tool` — there is no worker `tools/list` path, so "the
same endpoint and auth" was aspirational. New `McpTransport` abstraction in `julep/mcp_auth.py`
land: `list_tools()` + `call_tool()`, built from one place that resolves server URL + headers
(+ `secret://` refs) from worker config — the *same* transport instance serves runtime calls,
worker preflight, and (via the CLI) freeze-time snapshots. `mint_token` gains a **discovery
scope** (`tools/list`, deterministic idempotency key `preflight:{workflow_id}:{server}`), so
verifier-side servers can distinguish discovery from invocation.

Endpoint/header config stays **worker-side config** (`[tool.julep.mcp.servers]`), not release
content — releases stay portable across environments; the preflight compares *frozen tool
identity* against whatever surface the configured server presents.

### 4.3 Enforcement: run-start preflight (worker-side), replay-safe (finding 7)

A preflight activity runs as the first *scheduled activity* of a run whose release references
MCP tools:

- Worker-side (network path + signing key); per-worker cache, 30 s TTL; transport errors
  retry under the normal activity retry policy.
- Mismatch ⇒ typed `tool_surface_mismatch`: terminal `failed`, machine-readable detail
  (server, tool, frozen vs fresh definition hash, human-readable diff), **zero user/tool
  effects** (framework setup — capability verification, trajectory init — may already have
  run; no reasoner or tool activity has).
- **Refusal is an asynchronous terminal state.** `POST /v1/runs` keeps returning `accepted`;
  the refusal lands via the normal terminal path and is visible in `GET /v1/runs/{id}`,
  `GET .../result?wait_s=`, and SSE. Documented as such — no synchronous refusal promise.
- **Replay/versioning discipline:** absent policy field in `FlowInput` ⇒ legacy `off` (old
  histories replay unchanged); the new activity is gated behind `workflow.patched("mcp-preflight")`;
  the effective policy is captured **from the release** at freeze (`[tool.julep.mcp] preflight`
  at author time), overridable only by an authorized submission parameter; and
  `preflight = {policy, completed, surface_digest}` rides `FlowInput` across continue-as-new so
  later segments never silently re-evaluate under different configuration.

**Activation-time advisory:** `POST /v1/deployments` runs the same check best-effort from the
control plane when reachable, storing per-server status on the deployment record (schema
addition — current activation rows carry only lane/release/timestamps). Advisory only.

### 4.4 Mid-run drift (finding 9)

No rechecks mid-run or across CAN. Call-site drift signatures (tool-not-found; server-side
input-schema rejection) become **`ToolSurfaceDrift`**, added to the harness's non-retryable
classification — and, critically, **detected through the `ActivityError` cause chain in
AgentWorkflow's tool dispatch**, projected as a typed failure and **re-raised**: today
AgentWorkflow converts tool activity errors into observations for the next model round, which
would swallow the drift signal into the loop. Tested on both the sequential and concurrent
(READ) dispatch paths. Author contract unchanged: interface change ⇒ redeploy referencing
flows; in-flight runs assume the frozen surface.

## 5. dotctx agents on AgentWorkflow (finding 6 — no second loop)

### 5.1 Binding (unchanged surface, corrected validation)

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

Packages stay mem-mcp-shaped (bare keys; contracts in `tools.pyi`). Freeze: snapshot bound
servers; resolve every bare key (unbound/unknown ⇒ loud error); validate `tools.pyi` stubs
against the frozen `inputSchema` by **exact canonical-schema equality** — the existing
`ToolSchemaExpectation` check (`freeze.py`) already does this and MUST NOT be weakened to
name-subset matching (finding 2); record the **alias map** bare-key → wire `ToolRef` in the
release. The model-visible tool name is the bare key, mapped to the MCP wire name at dispatch.

### 5.2 Execution: lower to the existing agent loop

`reasoner_to_flow` lowers a tool-bearing reasoner to the **`app` shape running
`AgentWorkflow`** — bounded by `max_rounds` when set, by `[tool.julep] agent_round_cap`
(default 32) for `agent: true`. No new IR node for the loop itself; reasoners without tools
lower exactly as today (hash stability preserved).

`AgentInput` is extended to carry: the frozen **alias map**, frozen tool definitions
(schemas presented to the provider under bare names), and frozen contracts. Inherited from
AgentWorkflow, free of charge: deterministic activity cids (the `mcp_auth` `idk` binding),
**READ-contract calls concurrent / writes serialized** (v1 keeps this — the v1-draft
"sequential-only" idea was a regression, §10 Q4), `require_tool_call`, budget guard, and the
existing **mid-loop continue-as-new seam** (a loop inside a new flow node would have had none —
FlowWorkflow only CANs between root-flow returns).

Two AgentWorkflow gaps close as part of this (finding 10):

- **Real output validation**: final answers validate against the reply schema with an actual
  JSON-Schema validator, re-prompting within `output_retries` (today the loop only checks the
  reply is a dict; schemas are prompt-injected when tools are present).
- **Durable canonical transcript**: tool-call ids, names, arguments, result refs, and ordering
  persist and ride across CAN independently of prompt-context truncation (today incomplete
  tool turns can be reconstructed lossily).

### 5.3 Declarations blob v2 (finding 8)

Blob schema v1 carries reasoners + renderers only, and hydration writes into a process-global
registry keyed by name. For generic workers to run zero-code agents, the blob format bumps to
**v2**: adds alias maps, frozen tool definitions/contracts, and tool grants; hydration becomes
**release-scoped** (keyed by declarations hash) instead of process-global name identity, so two
releases defining the same logical reasoner differently cannot conflict on one worker; and
hydration happens before `resolveAgentSpec` (which today does not accept a declarations ref —
it gains one).

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
| Run `secrets` submitted while payload encryption is off | 400 at submission (feature requires the codec) | `POST /v1/runs` |
| Vault transient outage, cached value | stale served ≤ 15 min, then fail closed | worker logs |
| Non-worker key reads a value; worker key off-allowlist | 403 | API |
| Worker key on non-secret routes | 403 | API |
| Freeze: unbound key / unknown tool / stub-schema mismatch | freeze error | `julep plan/apply` / `deploy()` |

## 7. Testing

- **Retry authority**: unasserted contract never yields attempts > 1 regardless of hints;
  asserted paths unchanged (regression tests around `_retry_policy_for`).
- **Pin check**: hash-equality matrix (identical ⇒ pass; any schema/annotation/name change ⇒
  typed mismatch with diff); normalized-annotation persistence round-trips through release
  JSON; `names`/`off` policies honored.
- **Preflight**: fixture MCP server mutated between freeze and run ⇒ refused asynchronously
  with detail; `workflow.patched` gating replays old histories cleanly; policy + completed +
  digest carried across CAN; 30 s cache; transport-error retries.
- **Transport**: one transport serves call/list/snapshot; discovery-scope tokens verified;
  header `secret://` resolution per call.
- **Run secrets**: non-persistence (stored `input_ref`, `GET /v1/runs`, SSE, and projection
  values never contain submitted values — assert against the raw store); submission refused
  when payload encryption is off; step-0 resolution precedence over vault and env; threading
  through child flows, AgentInput, CallToolInput, and both CAN paths; value-hash cache
  identity (header-swap collision test); scrubber registration of run-supplied values;
  direct-start parity (locally-constructed FlowInput with secrets).
- **Vault**: role parsing back-compat (`:admin` unchanged; `:worker`; junk third field errors);
  route audit (worker key 403 everywhere but value fetch); allowlist fail-closed; AAD binding
  (row/generation swap fails to decrypt); key-ring rotation + `reencrypt-secrets` sweep +
  retirement guard; resolver chain, TTL, bounded stale-if-error, immediate eviction on
  401/403/404/410/archive/delete; scrubber catches exact/base64/urlencoded echoes at
  trajectory, projection, activity-failure, and transport-diagnostic boundaries.
- **Agent lowering**: tool-bearing reasoner ⇒ app/AgentWorkflow with alias map (goldens);
  non-tool reasoners byte-identical lowering; alias-mapped dispatch; READ-concurrent
  determinism preserved; `ToolSurfaceDrift` re-raise on sequential AND concurrent paths;
  JSON-Schema output validation + `output_retries`; canonical transcript across CAN.
- **Declarations v2**: golden blob; release-scoped hydration (two conflicting releases coexist
  on one worker); generic worker (no `WORKER_APPLICATION`) runs the issue-dedup agent from the
  release alone.
- **Live**: issue-dedup agent, vault-referenced header, submitted through `/v1/runs`, SSE to
  terminal; then a drift injection (restart tools server with a changed schema) ⇒ typed refusal.

## 8. Sequencing

- **PR-B0 (first, small):** retry-authority fix — unasserted contracts cap at 1 attempt; +
  normalized-annotation persistence in `FrozenTool`/releases. Fixes a live issue independent of
  everything else.
- **PR-A: vault-lite** — migration (v9+), `/v1/secrets` (operator credentials), key roles +
  route audit, allowlist, `julep/secrets.py` resolver + scrubber, run-secrets ingest at
  `POST /v1/runs` (strip-before-store, encryption-required check), vault key ring +
  `db reencrypt-secrets`, doctor check, docs.
- **PR-B: surface contract** — `McpTransport` unification + discovery scope, `pin` check,
  preflight activity behind `workflow.patched`, policy pinning + CAN carriage, run-secret
  threading through FlowInput/AgentInput/CallToolInput/child starts/CAN + identity-complete
  transport/preflight cache keys, drift classification + AgentWorkflow re-raise, activation
  advisory (deployment schema add), docs.
- **PR-C: dotctx agents** — binding config + freeze validation + alias map, lowering to
  app/AgentWorkflow, `AgentInput` extension, output validation + canonical transcript,
  declarations blob v2 + release-scoped hydration, eval fakes, issue-dedup example upgrade,
  docs. Depends on B0/B; consumes A for headers.

## 9. Out of scope (v1)

Directional JSON-Schema `compat` mode (future alpha); OAuth auto-refresh; egress
proxies/placeholders; julep-side tenant secret storage (owners/audiences/grants/templates/
binding slots — §3.5); per-secret *host* binding; secret version history + webhooks;
LISTEN/NOTIFY rotation push; MCP *server* authoring; sourcing `worker_secret_environment`
(K8s) from the vault.

## 10. Open questions — resolved by review

1. **Stale-if-error**: bounded — 15 min, transient failures only; auth/not-found/archive/delete
   evict immediately. Revocation cannot coexist with unbounded stale reads.
2. **Admin keys barred from reads**: keep. Static-config keys mean admin need not inherit read;
   break-glass = deliberately provisioning a worker-role key.
3. **Policy pinning**: source of truth is the immutable release; absent field = legacy off;
   authorized submission may override; carry effective policy + result digest across CAN.
4. **Sequential-only rounds**: rejected — preserve AgentWorkflow's deterministic
   READ-concurrent / write-serialized dispatch.
5. **`destructiveHint` absent→true**: not drift (absent already means true under MCP
   defaults); normalize annotations per negotiated protocol before comparison; annotations
   never grant or remove retry authority either way.

## 11. Review log

**v1 → v2 (codex `gpt-5.6-sol@high`, adversarial review at `7def6182`):** verdict
needs-rework (S3), unsound (S4), needs-rework (S5). All 13 findings incorporated:
(1) retry authority severed from unasserted hints + annotation persistence [→§4.1, PR-B0];
(2) structural compat check replaced by `pin` hash equality, `tools.pyi` validation stays
exact-canonical [→§4.1, §5.1]; (3) `McpTransport` unification, worker `tools/list`, discovery
scope, async refusal, "zero user/tool effects" wording [→§4.2–4.3]; (4) single role token
(comma parsing preserved), route audit, worker read allowlist, no worker list endpoint
[→§3.2]; (5) rotation promises split by consumer class, bounded stale-if-error, immediate
revocation eviction, generation-keyed cache [→§3.3–3.4]; (6) S5 reframed onto AgentWorkflow;
no second loop; mid-loop CAN inherited [→§5.2]; (7) `workflow.patched` gating, legacy-off
default, release-pinned policy, CAN carriage [→§4.3]; (8) declarations blob v2 with bindings +
release-scoped hydration [→§5.3]; (9) `ToolSurfaceDrift` cause-chain detection + re-raise out
of the agent loop [→§4.4]; (10) real JSON-Schema output validation + durable canonical
transcript [→§5.2]; (11) dynamic value scrubber at four boundaries + honest scope [→§3.3];
(12) dedicated vault key ring, AAD binding, re-encryption + retirement protocol [→§3.1];
(13) factual fixes (`TEMPORAL_PAYLOAD_KEYS`, config ALLOWED_KEYS additions, deployment-record
schema addition, migration numbering) [throughout].

**v2.1 → v3 (§3.5 multi-tenant):** a second focused review (codex `gpt-5.6-sol@medium`)
judged the v2.1 run-scoped binding map **unsound** (self-asserted tenant identity via
`merge_principal`; name-level confused deputy incl. global-secret exfiltration; unstable name
identities over durable runs; allowlist globs ≠ tenant isolation; incomplete FlowInput
carriage; underspecified cache identity; forgeable `mcp_auth` claims on direct starts). A
grant-based v2.2 draft addressed every finding, then was superseded by the owner's
simplification: **caller-supplied per-run secrets**, which removes shared tenant storage and
with it the entire authorization surface the findings attacked. The vault reverts to
operator/infra credentials only.
