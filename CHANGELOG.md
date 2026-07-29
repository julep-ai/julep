# Changelog

## 3.0.0rc6 (unreleased)

### Added

- Embedded runs can expose a frozen `EmbeddedRun` envelope through
  `arun_detailed` / `run_detailed`, stream projection events to a synchronous
  sink, and retain caller-owned projections across failures (FEEDBACK 38).
- `julep.embedded.load_pipeline` compiles standalone `.ctx` packages without a
  project file or Kubernetes-derived application naming (FEEDBACK 37).
- Configured `llm_caller` values now participate in embedded caller precedence,
  and `LlmResult`, `LlmCallMeta`, `AttemptMeta`, and `EmbeddedRun` are root-public.
- `LlmUsage` gives model-call metadata a typed prompt/completion/total and cache
  token shape. The LiteLLM caller captures that usage, preserves reported
  prices, and can fail-soft derive missing prices from LiteLLM's pricing map.
- `EmbeddedRun` now includes aggregate LLM usage and total price, with explicit
  reported/derived/mixed/unknown status and completeness fields (FEEDBACK 38).
- `julep run <package>.ctx` now records its local projection in the run cache,
  including failed runs, so the same run id is available to `julep trace`.
- Foreground runs now honor `WorkerContext.trajectory_sink`, trajectory blob
  storage/redaction, and `on_attempt`; `TrajectoryRecorder` and
  `InMemoryTrajectoryStore` can capture caller-named embedded runs (FEEDBACK 38).
- `julep apply --activate` activates every lane of the release it just
  published, over the connection `--api-url`/`--api-key` already established,
  instead of printing one `julep activate` command per lane. Explicit
  activation stays the default. Without a control-plane connection the flag
  exits 2 before publishing anything. Every lane is attempted even after one
  fails, so a partial rollout prints which lanes moved and which did not and
  exits 1. Note the sharp edge: a control plane configured with
  `JULEP_SERVER_HELM_CHART` re-reconciles the lane on activation and answers
  `409` unless it reproduces the release's frozen `deployment_config`
  byte-identically — both `--activate` and `julep activate` now name that cause
  instead of reporting a bare conflict.

### Changed

- **Behavior change: a hand-run worker now fails closed on Temporal payload
  encryption.** `TEMPORAL_PAYLOAD_ENCRYPTION_REQUIRED` defaulted to `true` on
  the control plane and `false` on the worker, so a worker joined the plane the
  server encrypts with a plaintext converter unless the operator remembered to
  set the variable. The worker default is now `true`, matching the server:
  `julep worker` (and `julep artifact worker`) refuse to start without
  `TEMPORAL_PAYLOAD_KEYS`/`TEMPORAL_PAYLOAD_KEY_ID`, and `serve()` refuses to
  poll even for settings assembled in code rather than from the environment.
  The documented opt-out is unchanged: set
  `TEMPORAL_PAYLOAD_ENCRYPTION_REQUIRED=false` to run against a deliberately
  plaintext Temporal. Deployed workers are unaffected — the Helm path already
  hardcoded encryption on — as are `julep serve api --local`, `julep dev up`,
  and `create_local_app`, which set the opt-out (or a keyring) explicitly. Ad
  hoc Temporal *client* connections (`julep run` against a remote env) keep the
  permissive default.

### Fixed

- Embedded retries now honor declared exponential backoff by default; direct
  dry-run callers can pass `sleeper=None` for record-only behavior (FEEDBACK 38).
- A failing Helm smoke test now reports the smoke-test Job's logs. The
  reconciler fetches them out of band on failure only, by label selector
  (`kubectl logs --selector job-name=<release>-smoke`), because the Job's Pod
  carries a generated suffix and the chart retains failed Jobs. Log retrieval
  can never decide pass/fail: a missing `kubectl`, a denied RBAC rule, or an
  empty log leaves the original Helm failure intact with a
  `smoke-test logs unavailable` note (FEEDBACK 28).

## 3.0.0rc5 (unreleased)

### Breaking

- **The `julep[yglu]` extra is removed.** `.ctx` `settings.yaml` files using
  `!? $env.get("VAR", default)` (including nested `$env.get` fallbacks) keep
  working via a built-in evaluator with the same deterministic `$env` binding
  contract (`set_default_env` / explicit `env=`), now thread-safe. Any other
  yglu tag (`!if`, `!for`, `!concat`, `!merge`, `!()`) or expression raises an
  actionable error: only `$env.get(...)` is supported, and env-dependent config
  should move to run input or metadata. Background: yglu's yaql dependency
  imports `pkg_resources`, removed in setuptools 81+, making the extra
  uninstallable-in-practice on current toolchains (FEEDBACK 34).

### Added

- `julep activate --env <env> --lane <lane> --release <hash>` activates a lane
  on the control plane (rollback = activate a previous release hash), and
  `julep apply` now prints the exact activation command per lane after
  `traffic unchanged`. New `JulepClient.activate_deployment` /
  `list_deployments` on both sync and async clients (FEEDBACK 31).
- Config-gated unauthenticated readiness probe `GET /v1/health/ready`
  (`JULEP_UNAUTHENTICATED_READY=1`) running the same PostgreSQL / artifact
  store / Temporal checks as the authenticated `/v1/ready`, for Kubernetes
  HTTP probes (FEEDBACK 32).
- Tag-triggered PyPI publish workflow (`.github/workflows/publish.yml`).

### Changed

- `julep status` distinguishes "not observable from here" from unhealthy:
  lanes whose Temporal endpoint cannot be reached from the operator machine
  (e.g. cluster-local DNS) report `unobservable` with a warning and exit 0;
  genuinely degraded lanes still exit 3. New `--skip-temporal` flag skips
  direct Temporal probing entirely (FEEDBACK 30).

### Fixed

- `julep apply` no longer fails after a *successful* Helm smoke test on
  Helm 3.21 (`helm test` is run without `--logs`; successful smoke Jobs are
  retained for inspection) (FEEDBACK 28).
- The generic worker image installs the `mcp` and `server` extras required by
  schema-v2 runtime preflight, and the image build now fails fast on a broken
  `julep.execution.bundle_worker` import (FEEDBACK 29).
- Mixed code + configured-`.ctx` applications no longer pin the merged
  declarations hash into `WORKER_RUNTIME_DECLARATIONS_HASH`; workers verify
  against the code-only application hash and start instead of failing closed
  (FEEDBACK 33).
- WASM pure execution hardened (bounded resources, source admission) without
  breaking legacy bundle resolution or Temporal replay; release publication is
  retry-safe.

### Documentation

- New [Embedded execution](docs-site/content/docs/deploy/embedded.md) page: the
  admission rule (embedded Julep for prompt calls; remote durable Julep when
  Julep replaces orchestration), the in-process `prepare_local_pipeline` path,
  the supported recipe for a `.ctx` package with no `julep.toml`, the
  accepted-IR contract (which shapes raise `LocalExecutionUnsupported`), and the
  two DBOS shapes side by side — `LocalPipeline.arun` inside a consumer-owned
  `@DBOS.step` versus the nested Julep-owned workflow of `run_flow_dbos`
  (FEEDBACK 36, 39). The page states up front that `arun` returns the value only:
  usage, cost, attempts and projection are not surfaced yet (FEEDBACK 38).
- The Kubernetes payload-encryption Secret is documented for the first time:
  keyring grammar, a `kubectl create secret generic` recipe with the chart's real
  `keyring` / `active-key-id` key names, the `julep keygen` → Secret bridge, and
  key rotation.
- Corrected the security posture of the managed path: `julep apply` hardcodes
  payload encryption on, so `TEMPORAL_PAYLOAD_ENCRYPTION_REQUIRED=false` is
  honored only by a hand-run server or worker. A new "Mandatory and optional
  controls" section states what is actually enforced for API keys (fail-closed),
  bundle signing (verified only where a bundle reference exists), the vault,
  worker secret allowlists, and MCP preflight.

### Development

- The test suite is invocation- and order-independent. `pythonpath = ["."]` makes
  a bare `pytest` collect identically to `python -m pytest` (previously 14
  collection errors), and `isolate_default_registry` is now autouse, so tests
  that register reasoners/renderers/tool expectations no longer leak
  `DEFAULT_REGISTRY` state into later tests. `CONTRIBUTING.md` documents the
  canonical command (FEEDBACK 35).

## 3.0.0rc4 (2026-07-27)

First release published via PyPI after rc2; see git history for details.
