# Julep System Review: mem-mcp Dogfood Direction

**Date:** 2026-07-13
**Decision:** move episode summary and one-liner generation to Julep on Temporal;
keep every other mem-mcp pipeline on DBOS for this slice.

## Findings

### 1. Consolidate legacy authoring surfaces later — deprioritized

Julep still carries older flow, agent, and `ca`-era entry points. Removing or
renaming them before a production consumer has exercised the replacement would
optimize the public surface without validating the operational path. Preserve
compatibility through the dogfood migration and revisit consolidation after the
summary lane has completed a rollback window.

### 2. Pursue broad DBOS/Temporal parity later — deprioritized

The two runtimes do not need feature-for-feature symmetry. DBOS remains the
engine for existing mem-mcp pipelines, RECORD execution, and recovery. Temporal
is introduced behind one routed boundary. Shared contracts should cover inputs,
outputs, idempotency, and observability; runtime internals may remain different.

### 3. Generalize the recovery IR later — deprioritized

The current summary migration does not justify a new cross-engine recovery IR
or a transactional outbox. Starts are intentionally at-least-eventual: producers
enqueue after commit and the existing minute sweep repairs missed starts. Build
a broader recovery abstraction only after a second production pipeline proves
the repeated need.

### 4. Make an application the deployment unit

Add explicit `Application` and generic `PipelineSpec[Input, Output]` objects in
`julep.app`. A pipeline declares its flow, reasoners, capability manifest,
logical lane, and eval packages. Compilation is deterministic and rejects
duplicate names. This is an ordinary object model—not another decorator or AST
discovery path.

`julep plan`, `julep apply`, and `julep status` become the application-level
path. `plan` reports artifact, MCP-schema, Helm/KEDA, and runtime drift. `apply`
publishes immutable bundles and a content-addressed release manifest, then
reconciles one inactive Helm release per lane. It does not switch mem-mcp route
state. `status` combines the published release, Kubernetes/KEDA state, and
Temporal backlog/run state.

### 5. Treat the Temporal platform as production infrastructure

Promote the existing EKS demo into reusable Terraform and Helm configuration:
private EKS access, private encrypted RDS dedicated to Temporal, KEDA, ECR, an
S3 CAS, private networking, Secrets Manager integration with apply-time
Kubernetes materialization, and 14-day Temporal
history retention. CI supplies an immutable worker image digest. Terraform owns
clusters and shared services; Julep owns immutable application artifacts and
lane Helm reconciliation.

Every Temporal client and worker uses an AES-256-GCM payload codec. Envelopes
carry a key ID so an active key can rotate while older histories remain
decodable. S3 and RDS use KMS encryption at rest.

### 6. Dogfood episode summaries as one routed lane

Define `episode_summary` and `episode_one_liner` as independent pipelines on the
`summary` lane. Remove unused temperature values from their dotctx packages and
give both typed output schemas. The only application-facing state is:

```text
{pipeline, engine: hold|dbos|temporal, generation, release_hash}
```

Episodes keep independent `summary_generation` and `one_liner_generation`
counters. Runs pin route generation, source hash, and immutable release digest.
Stable workflow IDs have the form
`mem:episode-summary:{store}:{episode}:g{generation}`. A duplicate start is an
accepted result; workflow-ID reuse is allowed only after a failed terminal run.

One private authenticated `memory-tools` MCP service owns four operations:
read/write summary and read/write one-liner. Five-minute Ed25519 JWTs are scoped
by issuer, audience, store, tool scopes, and optional viewer identity. Julep's
deterministic activity idempotency key is forwarded. Writes reject stale source,
generation, or route data and all cross-store access while retaining exact-result
idempotency, normalization, and conditional writes.

After a summary transaction commits, the shared Python starter starts the
linked one-liner workflow. The episode trigger only invalidates and advances
generation. Known mutations, backfills, bookkeeping, and the orphan sweep call
the same router after commit. Legacy DBOS summary code remains available for one
rollback window but receives no active production work after cutover.

### 7. Make rollout and health route-aware

Run both prompt eval suites through mem-mcp's production `LlmCaller` and require
no regression from the native baseline. Staging must exercise workflow replay,
provider failure, concurrent edits, `0 -> 4 -> 0` KEDA scaling, global model
concurrency at most four, stale-write rejection, and duplicate suppression.

Production intentionally has no shadow or percentage canary:

1. Apply the inactive immutable release.
2. Set the route to `hold` at a new generation.
3. Drain DBOS summary and one-liner work.
4. Route all new work to Temporal and immediately run the orphan sweep.
5. Reconcile, then scale the DBOS summary worker to zero.

Rollback creates another `hold` generation, rejects stale Temporal writes,
drains or cancels old runs, restores the DBOS route/workers, and runs the repair
sweep. `/health/ready` is unchanged. `/health/background` becomes route-aware
and degrades for Temporal/MCP unavailability, terminal-error spikes, or an
oldest missing/queued summary age over five minutes.

## Next slice

After the summary lane completes its rollback window, migrate `record_plan`,
`record_plan_asks`, and `record_plan_rest` as whole Temporal pipelines. Their
successful results continue enqueueing the existing DBOS RECORD executor.
RECORD execution and recovery remain out of scope.

## Explicit non-goals

- No broader DBOS retirement.
- No public Memory Store MCP contract change.
- No production shadow traffic, percentage rollout, or canary.
- No transactional outbox, new recovery IR, or internal-service split.
- No route mutation as a side effect of `julep apply`.
