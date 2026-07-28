# Changelog

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

### Development

- The test suite is invocation- and order-independent. `pythonpath = ["."]` makes
  a bare `pytest` collect identically to `python -m pytest` (previously 14
  collection errors), and `isolate_default_registry` is now autouse, so tests
  that register reasoners/renderers/tool expectations no longer leak
  `DEFAULT_REGISTRY` state into later tests. `CONTRIBUTING.md` documents the
  canonical command (FEEDBACK 35).

## 3.0.0rc4 (2026-07-27)

First release published via PyPI after rc2; see git history for details.
