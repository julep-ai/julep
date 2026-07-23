# `ca` CLI v1.5 — deploy / status / run --env (outer loop)

> **For agentic workers:** TDD each component. Steps use `- [ ]`. Verify every plumbing signature against real source before coding — the references below are from exploration but confirm them.

**Goal:** Add the outer loop: `ca deploy <selector> --env` (freeze → publish bundle → record in a committed ledger), `ca status --env` (ledger + drift, exit 3 on drift), and `ca run <agent> --env` (execute a deployed agent against that env's Temporal). No infra rollout — the generic worker already runs.

**Architecture:** `ca deploy` makes an agent *available* (immutable, content-addressed, recorded); `ca run --env` *executes*; `ca status` shows *what's where + drift*. Builds on existing plumbing: `deploy()` (mints `artifact_hash`), `Deployment.publish(store)` (pushes bundle to CAS), `run_flow(client, flow_json, manifest_json, task_queue=)` (frozen IR travels in the workflow input). The new layer is a **deploy ledger**, which does not exist today.

**Decisions (locked in brainstorming):** freeze+publish+ledger (no infra rollout) · committed lockfile `.julep/deploys/<env>.json` · this increment = deploy + status + `run --env` · freeze mirrors `_cmd_freeze` (`strict=False`, no caps manifest) · drift = re-freeze + compare `artifact_hash`.

---

## Reference plumbing (confirm against source)

- `deploy(flow, snapshot=None, *, tools=, reasoners=, capabilities=, strict=True, ...) -> Deployment`; `Deployment.flow_json`, `.manifest_json`, `.artifact_hash` (`sha256:…`), `.publish(store) -> sets .bundle_ref`. (`composable_agents/deploy.py:212,455`)
- CAS: `LocalDirCAS(root)`, `S3CAS(bucket, prefix=...)`; `CASStore.put/get/has`. (`composable_agents/cas.py:39,54,118`)
- `snapshot_from_tools(tools)` builds an `McpSnapshot` from `@tool` objects (confirm exact name in `composable_agents/agent.py`). The live agent + its tools exist ONLY in the user's interpreter → freeze must happen in the subprocess resolver.
- `run_flow(client, flow_json, manifest_json, *, session_id, input=None, task_queue="composable-agents", bundle=None, ...) -> Any`. (`composable_agents/execution/harness.py:1572`)
- Temporal client: `from temporalio.client import Client; await Client.connect(address, namespace=...)`. `temporalio` is in the `dev` extra; gate the import.
- Existing `ca/_resolve_child.py` already imports user modules + finds the agent by `FlowLike.name`; extend it with a freeze+publish mode.

**Verifiability boundary:** `--env local` (LocalDirCAS + ledger + drift) is fully testable here. `S3CAS` publish needs `boto3` (the `store` extra, maybe not installed) — gate it. `run --env <cloud>` needs a live Temporal — build + unit-test with a fake client; mark integration-pending.

---

## File structure

```
composable_agents/ca/config.py        EXTEND: EnvConfig dataclass + JulepConfig.envs (parse [tool.julep.env.<name>]); implicit `local`
composable_agents/ca/ledger.py        NEW: DeployRecord + read_ledger/upsert_record (.julep/deploys/<env>.json)
composable_agents/ca/_resolve_child.py EXTEND: a "freeze" action that deploy()s the agent, publishes to the CAS, prints {artifact_hash, flow_json, manifest_json, bundle_ref}
composable_agents/ca/deploy.py        NEW: freeze_agent(cfg, name, env) (drives subprocess freeze) + deploy_agents(cfg, names, env) (freeze+publish+write ledger)
composable_agents/ca/status.py        NEW: status_for_env(cfg, env, names) -> rows + drift; exit-code helper
composable_agents/ca/temporal_run.py  NEW: run_on_env(cfg, name, env, value) -> result (Temporal client + run_flow); gated temporalio import
composable_agents/ca/cli.py           EXTEND: `deploy`, `status` commands + `--env` option on `run`
.gitignore                            ADD: .julep/runs/ and .julep/cas/ (ignored); .julep/deploys/ stays tracked
tests/cli/test_envconfig.py test_ledger.py test_deploy.py test_status.py test_temporal_run.py test_deploy_cmd.py
```

---

## Task 1 — Env config (`config.py`)

**Contract:** add `EnvConfig(name, temporal_address: str|None, temporal_namespace: str, task_queue: str, cas: str|None, langfuse_host: str|None)` and `JulepConfig.envs: dict[str, EnvConfig]`. Parse `[tool.julep.env.<name>]` tables (pyproject + julep.toml override, same precedence as the rest of config). Always include an implicit `local` env (cas defaults to `.julep/cas`, no temporal). `cas` is a URI: `s3://bucket/prefix` or a local path (default `.julep/cas`).

- [ ] Test (`tests/cli/test_envconfig.py`): defaults give `envs["local"]` with `cas` ending `.julep/cas`, `temporal_address is None`; a `[tool.julep.env.staging]` table parses address/namespace/task_queue/cas; `julep.toml` overrides an env field.
- [ ] Implement; keep existing `JulepConfig` fields/behavior unchanged. `ruff` + `mypy --strict` clean.
- [ ] Commit `feat(ca): env config tables for deploy/run targets`.

## Task 2 — Deploy ledger (`ledger.py`)

**Contract:** `DeployRecord(agent, artifact_hash, flow_json: dict, manifest_json: dict, bundle_ref: list[dict]|None, deployed_at: str)` — the frozen IR is stored in the record so the committed ledger is **self-describing** and `run --env` replays the *deployed* artifact with no re-freeze (accept the larger ledger file; it IS the deploy artifact). ISO ts passed in by the caller — never generate time inside a workflow context, but the CLI is plain Python so `datetime.now(timezone.utc).isoformat()` is fine here). `ledger_path(root, env) -> Path` = `.julep/deploys/<env>.json`. `read_ledger(root, env) -> dict[str, DeployRecord]` (empty if missing). `upsert_records(root, env, records) -> None` (merge + write pretty JSON, stable key order). `deployed_hashes(root, env) -> dict[str,str]` convenience.

- [ ] Test (`tests/cli/test_ledger.py`): upsert two records → read back; upsert again updates one, keeps the other; missing ledger → `{}`; JSON is stable/sorted.
- [ ] Implement; `ruff` + `mypy --strict` clean.
- [ ] Commit `feat(ca): committed deploy ledger (.julep/deploys/<env>.json)`.

## Task 3 — Subprocess freeze mode (`_resolve_child.py` + `deploy.py`)

**Contract:** extend `_resolve_child.py` to accept an action (e.g. payload `{"action":"freeze", "root","src","name","cas"}`): find the agent (existing logic), build its snapshot from its tools (`snapshot_from_tools` or equivalent — confirm), `dep = deploy(flow_or_agent, snapshot, tools=<the agent's tools>, strict=False)`, construct the CAS store from `cas` (`LocalDirCAS(path)` for a local path / `S3CAS(...)` for `s3://`), `dep.publish(store)`, then print `{"artifact_hash": dep.artifact_hash, "flow_json": dep.flow_json, "manifest_json": dep.manifest_json, "bundle_ref": dep.bundle_ref}`. On error print `{"error": ...}`. `deploy.py`: `freeze_agent(cfg, name, env) -> FrozenArtifact` runs the subprocess in freeze mode; `deploy_agents(cfg, names, env, *, now_iso) -> list[DeployRecord]` freezes+publishes each and upserts the ledger.

- [ ] Test (`tests/cli/test_deploy.py`, **local CAS, fully verifiable**): using the `sample_module` fixture + a `[tool.julep.env.local]`, `deploy_agents(cfg, ["triage"], "local", now_iso="2026-06-23T00:00:00Z")` returns a record with a `sha256:`-prefixed `artifact_hash`, writes `.julep/deploys/local.json`, and the bundle lands under `.julep/cas/`. `freeze_agent` on an unknown agent → error surfaced, no ledger write.
- [ ] Implement; gate the `s3://` path so a missing `boto3` raises a clear "install the `store` extra" message; local path needs no extra. `ruff` + `mypy --strict` clean.
- [ ] Commit `feat(ca): subprocess freeze+publish + deploy_agents ledger writer`.

## Task 4 — Status + drift (`status.py`)

**Contract:** `status_for_env(cfg, env, names) -> list[StatusRow]` where `StatusRow(agent, deployed_hash: str|None, current_hash: str|None, state: "clean"|"drift"|"undeployed")`. Drift = re-freeze current source (`freeze_agent`) and compare `artifact_hash` to the ledger. `status_exit_code(rows) -> int`: `0` all clean/undeployed-and-not-selected, `3` any drift. (Undeployed selected agents are reported but do not gate.)

- [ ] Test (`tests/cli/test_status.py`, local): deploy `triage` to `local`, then status shows `triage` clean; edit triage's source so its hash changes → status shows `drift` and `status_exit_code == 3`; an agent never deployed shows `undeployed`.
- [ ] Implement; `ruff` + `mypy --strict` clean.
- [ ] Commit `feat(ca): ca status drift detection vs deploy ledger`.

## Task 5 — Run against an env (`temporal_run.py`)

**Contract:** `run_on_env(cfg, name, env, value) -> RunResult`. For `local`: fall back to the existing in-memory `run_agent_local` path (no Temporal). For a non-local env: load the deployed `flow_json`/`manifest_json`/`bundle_ref` from the ledger (error if not deployed), `Client.connect(env.temporal_address, namespace=env.temporal_namespace)`, `await run_flow(client, flow_json, manifest_json, session_id=<minted>, input=value, task_queue=env.task_queue, bundle=bundle_ref)`, return the result. Gate `temporalio` import with a clear message if missing. **The ledger must store `flow_json`/`manifest_json`** (extend the record or fetch from CAS by hash) so run doesn't need to re-freeze — confirm and wire whichever is simplest (storing them in the ledger record is fine for v1.5; note the size).

- [ ] Test (`tests/cli/test_temporal_run.py`): `local` env routes to the in-memory runner and returns events (reuse the Task-5 runner). For the cloud path, inject a **fake client** whose `execute_workflow` records the args and returns a canned result; assert `run_flow` is called with the deployed `flow_json` + `task_queue` from the env. (No live Temporal — integration-pending, stated in the test docstring.)
- [ ] Implement; `ruff` + `mypy --strict` clean.
- [ ] Commit `feat(ca): ca run --env via run_flow against a deployed agent`.

## Task 6 — CLI wiring + .gitignore (`cli.py`)

**Contract:** add `ca deploy <selector> --env <name>` (default `local`; freezes+publishes+records selected agents; prints each agent + short artifact_hash; exit 0, or 1 on any freeze error). `ca status --env <name> [selector]` (prints rows + state; `raise typer.Exit(status_exit_code(rows))`). Extend `ca run` with `--env <name>` (default `local`): local keeps today's behavior; non-local calls `run_on_env`, renders the trace tree from returned events if available, prints the Langfuse deep link. Add `.gitignore` lines `.julep/runs/` and `.julep/cas/` (keep `.julep/deploys/` tracked).

- [ ] Tests (`tests/cli/test_deploy_cmd.py`, local): `ca deploy triage --env local` exit 0 + `.julep/deploys/local.json` written; `ca status --env local` after deploy → exit 0 prints `clean`; `ca status` with a drifted source → exit 3; `ca run triage --env local` still renders a tree (unchanged local path).
- [ ] Implement; full `tests/cli` green; `ruff` + `mypy --strict` clean.
- [ ] Commit `feat(ca): wire deploy/status + run --env into the cli`.

## Task 7 — Gate

- [ ] `ruff check composable_agents/ca` clean.
- [ ] `python -m mypy --no-incremental --cache-dir=/dev/null composable_agents` strict-clean.
- [ ] `python -m pytest -q` — full suite green except the known pre-existing `test_env_builder` wasm-artifact failure.
- [ ] Local e2e: in a scratch module, `ca deploy triage --env local && ca status --env local` (clean) → edit source → `ca status --env local` (exit 3 / drift). Report output honestly; mark Temporal `run --env` as integration-pending.
