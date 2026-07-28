# Julep adoption feedback (from the mem-mcp wave-1 port, 2026-07-22)

Field notes from consuming julep 3.0.0rc4 (local editable, `julep3-post-port`) as the
first real control-plane consumer. Items marked **[in-branch]** are being fixed on
`julep3-post-port` as part of the port; the rest are open asks/wishlist.

> **Status 2026-07-23 (see FEEDBACK-REPLY.md in consuming repos):** effectively the
> whole ledger is implemented on `julep3-post-port`. Items 1–5, 7, 9, 13, 16–20 landed
> in the run_and_wait/local-api-mode batches (`Reasoner.replace` closes 8; pipeline
> lint + honest trace costs close 10 and 14; `MissingOutputSchemaWarning` closes 15;
> the durable dev supervisor + local-dev guide close 20 and 11); the tool-bearing-run
> findings 21–26 are fixed with cross-backend tests, `AgentTerminalError` (25), the
> public `LlmCaller` contract (24), and `LocalDirBlobStore`/`JULEP_BLOB_STORE_URL`
> (26, `5c5a2d92`). Still open: **item 6 only** (temporalio/pydantic-ai pin collision —
> consumers carry a uv override). Item 12 was wrong — the server default is already
> 8080, not 8000.

## Bugs / blockers hit

1. **[in-branch] `apply --publish-only` requires Helm/K8s config it never uses.**
   Config validation demands worker image, Helm chart, and the K8s payload-secret name
   before the publish branch is reached (`julep/cli/application.py:180,260`,
   `app_deploy.py:999`). A local/external-worker consumer can't publish without dummy
   values. Fix: deploy/reconcile fields optional unless reconciliation is requested.

2. **[in-branch] Eval runner breaks when a real `dotctx` distribution is installed.**
   The shim is skipped, but `evalrun.py:208` requires julep's exact `Sample` class
   (`dotctx_evals.py:285`); preload the real package and transitive imports want
   `dotctx.Context`, which the shim lacks. This is the flagship compat scenario
   (mem-mcp ships its own `dotctx`); `julep eval` was unusable there.

3. **[in-branch] No way to register a published release with the control plane.**
   `apply` publishes to the artifact store but nothing POSTs `/v1/releases`;
   `JulepClient` has no `publish_release`. Every consumer would hand-roll the curl.

4. **[in-branch] Publish-only prints no task queues.** Queues are rewritten to
   `<lane>-r<release-hash-prefix>` at publish (`app_deploy.py:271,843`) but
   `--publish-only` output omits them, and the worker polls exactly
   `TEMPORAL_TASK_QUEUE` — the operator has to reverse-engineer the queue name.

5. **[in-branch] Zero-code ctx pipelines cannot set an execution policy.** Default is
   4 reasoner attempts × 120 s activity timeout; a resilient `LlmCaller` (which julep
   itself recommends owning retries) needs `reasonerMaxAttempts=1`, but there is no
   `[pipeline.*.policy]` config surface.

6. **Dependency conflict with pydantic-ai.** `julep[temporal]` floors `temporalio>=1.21`
   while pydantic-ai (≤1.61.0) pins `temporalio==1.20.0` via its unconditional
   `[temporal]` extra — the two can't coexist without a uv
   `override-dependencies = ["temporalio>=1.21"]`. Worth documenting the workaround, or
   auditing whether the 1.21 floor is truly load-bearing.

## API footguns

7. **Idempotent run return ignores the requested pipeline.** `POST /v1/runs` returns the
   existing run for a reused `Idempotency-Key` without checking that `pipeline` matches
   (`server/routes/runs.py:181`). A caller submitting two pipelines from one workflow id
   silently gets pipeline A's run back for pipeline B. Ask: 409 on pipeline mismatch.

8. **`Reasoner` has no copy/replace API.** Rebinding a reasoner to a fallback model
   requires re-enumerating all ~18 constructor kwargs (see mem-mcp's
   `_reasoner_with_slug`); every new Reasoner field silently drops through such copies.
   Ask: `reasoner.replace(model=..., reasoning_effort=...)` that preserves unknown fields.

9. **`JulepClient` is sync-only.** Async consumers (DBOS workflows, FastAPI handlers)
   must wrap every call in `asyncio.to_thread`. Wishlist: an httpx.AsyncClient variant.

## DX / docs wishlist

10. **`julep lint` doesn't cover configured ctx pipelines** — it scans discovered code
    agents only (`cli/model.py:31`), so the zero-code path has no structural lint gate.

11. **No end-to-end local dev-loop guide for the control plane.** The working order
    (temporal dev server → `serve api --migrate` → publish + register → derive queue →
    `julep worker` with `WORKER_CONTEXT_FACTORY` → `start_run`) plus the full env
    contract (`TEMPORAL_PAYLOAD_KEYS`/`KEY_ID`/`ENCRYPTION_REQUIRED` on BOTH api and
    worker, shared `JULEP_EXECUTION_STORE_DSN` — worker projection only *warns* when
    unset and the API then never sees results — shared `file://` artifact store,
    `JULEP_BUNDLE_SIGNING_KEY`/`ALLOWED_SIGNERS`, admin `JULEP_API_KEYS` entry) had to be
    reconstructed from source. One guide page would have saved hours.

12. **`JULEP_SERVER_PORT` default 8000** collides with the most common app-server port;
    a less contended default (or a loud bind-failure hint) would help side-by-side dev.

13. **`julep serve api --local` (owner ask, 2026-07-22).** Local testing/prototyping
    surfaces are otherwise complete — `julep run` with offline echo stubs,
    `deployment.dry_run(...)` with injected fake/real tools+reasoners,
    `julep artifact run-local` for frozen JSON, and in-process API tests via
    `server/app.py:57` (InMemoryExecutionStore + local artifact store + fake
    TemporalGateway covering auth/releases/deployments/runs/SSE/secrets). The missing
    convenience is API **plus** real execution without Temporal+Postgres: a fake gateway
    tests HTTP but doesn't execute. Ask: `serve api --local` = in-memory store, local
    artifacts, and an interpreter-backed gateway that actually runs the flow.

14. **`trace --remote` shows a flat `$2.0000` cost for a single nano-model think-flow.**
    Repro: wave-1 `episode_summary` run (one `openai/gpt-5.4-nano` call) →
    `julep trace --remote <run_id>` renders `[ok] $2.0000`. Looks like a placeholder or
    default rate rather than real usage-derived cost; worth checking what the projection
    carries when the LlmCaller's usage meta lacks pricing.

15. **dotctx `.ctx` packages without `class Output` silently degrade to raw text.**
    `reply_schema` derives exclusively from `Output` (`dotctx_rich.py:850`); a package
    authored for a host that enforces structure in code (mem-mcp's pydantic-ai loops)
    loads "successfully" but returns unvalidated text. Ask: a load-time warning (or
    `julep ls` column) when a pipeline's reasoner has no reply schema.

## Findings from the first real tool-bearing agent run (report_issue_dedup, 2026-07-23)

The first live multi-round dotctx agent (real model, real MCP server, real tool calls)
hit five gaps the test suite's fakes never exercised. All five are fixed on
`julep3-post-port` with regression and cross-backend tests.

21. **[fixed] `TOOL_SCHEMA_DRIFT` false-positives against every FastMCP server.**
    Signature-derived servers always emit `additionalProperties: false`; `tools.pyi`
    cannot express it; verbatim hashing made every such pairing drift at freeze. The
    authoring-time gate now directionally ignores only an extra served marker in
    actual JSON-Schema positions. Instance data, literal property names, and an
    explicit expected close remain significant; the runtime preflight pin still
    hashes served definitions verbatim.

22. **[fixed] Transcript-scoped agents re-rendered the business template from each
    round's observation.** Round 2 of any templated agent died with
    `'<variable>' is undefined` (StrictUndefined) because `state.last` becomes the tool
    observation. New contract: templates always render from the ORIGINAL input; the
    opening transcript user turn carries the rendered ask; no trailing template turn;
    loop feedback (re-asks, which `transcript_for` excludes) rides a reserved
    `FEEDBACK_KEY` as a user turn. Rendering and feedback insertion now happen
    before the hard context budget on Temporal, DBOS, shared/local execution, and
    `serve api --local`. Scoped agents retain real tool observations inline within
    a segment and as blob refs across durable continuations. Also added
    `[pipeline.<name>].context_max_tokens` and a required
    `[pipeline.<name>].summarizer` dotctx path for `context: summary`.

23. **[fixed] The action classifier rejected schema-conforming final answers.**
    `reply_schema` + julep's own prompt guidance tell the model to return the bare
    `Output` object, but `interpret_reasoner_reply(strict=True)` only accepted finish
    via the `done`/`output` envelope — every real-model final answer became
    `controller_error`. In native-tools mode a dict reply with no reserved action keys
    now finishes; scalar and array finals work as well. Output-schema validation and
    re-ask own shape enforcement, malformed reserved action envelopes still fail,
    and native output schemas declaring top-level action keys are rejected. A
    configured local API acceptance test now covers template rendering, a native
    tool round, its observation, and the bare final reply.

24. **[fixed] LlmCaller contract widened without the type saying so.** Agent rounds call
    `llm(..., tools=...)` but `effects.LlmCaller` is still the 5-positional alias —
    rc1-era callers crash at runtime with "unexpected keyword argument 'tools'"
    (mem-mcp's caller fixed consumer-side). `LlmCaller` is now a public protocol
    with keyword-only `tools=None`; the configure-time 2/3/4/5-argument adapters
    forward it when supported and otherwise raise a targeted upgrade error.
    `SyncCoalescer` preserves it through buffered and BATCH paths.

25. **[fixed] Agent runs that end in `controller_error` still surface as COMPLETED runs.**
    The agent's terminal envelope (`{status, output, trace, rounds, cost}`) is the run
    result, so `run_and_wait` returns success for a failed loop and consumers must
    inspect `result["status"]`. `controller_error`, `max_rounds`, `over_budget`,
    `denied`, and `output_validation_failed` now raise public
    `AgentTerminalError` at generic APP/durable boundaries and mark local,
    Temporal, and DBOS runs/trajectories failed (Temporal keeps its existing
    `OutputValidationError` for exhausted output validation). `done` and
    `escalated` remain successful values; agent facades/evals retain their
    low-level value-envelope behavior.

26. **[fixed] Durable tool/sub-bearing transcript agents had no shipped blob store.**
    The original report overstated the scope: first-round terminal agents and inline
    local execution need no store. Temporal and DBOS agents do need one as soon as a
    tool or subflow observation is persisted as a transcript ref; without it they fail
    after the effect succeeds, and `InMemoryBlobStore` cannot survive worker restart or
    cross replicas. Julep now ships an async, tenant-partitioned, integrity-checked
    `LocalDirBlobStore` plus `blob_store_from_url(file://...)` and
    `JULEP_BLOB_STORE_URL` wiring for `WorkerServeSettings`, `julep worker`, and the
    standalone `run_worker` helper. `julep dev up` forwards an explicitly configured
    URL only to workers. Ambiguous factory-plus-env stores fail at startup. Docs call
    out that file storage is a single-host building block unless operators provide a
    coherent shared mount with hard-link/`fsync` support and compatible identities.
    It has no application-level encryption or garbage collector, and its root must
    remain stable for the lifetime of retained Temporal or DBOS records. DBOS wiring
    is explicit because Julep does not own its process entrypoint; the in-memory
    implementation remains tests/one-process only.

## Consumer plumbing that should move into julep (from the full-migration estimate, 2026-07-23)

Wave-1 left ~1.2–1.8k LOC of projected consumer-side glue for a full mem-mcp migration.
Most of it is generic; candidates to absorb, ranked:

16. **`JulepClient.run_and_wait(...)` + an async client.** mem-mcp's `julep_runs.py` is
    ~100 lines of submit → poll(`get_result`, wait_s<client-timeout) → deadline →
    terminal-status triage → unwrap that every consumer will rewrite. One client method
    with typed terminal errors deletes the file. (Supersedes/absorbs item 9.)

17. **LiteLLM caller adapter owning the `@effort` → provider payload bridge.** mem-mcp's
    worker glue borrows a private function (`dotctx.__main__._prepare_litellm_payload`)
    for slug + reasoning-payload mapping (OpenRouter nested `reasoning`, Fireworks
    `extra_body`, temperature clamps). `julep.llm.litellm_caller()` would serve every
    LiteLLM shop and delete the borrowed bridge.

18. **Tiered-model fallback as an LlmCaller combinator.** On top of
    `make_resilient_llm_caller`: `with_model_ladder(caller, models=[...], classify=...)`
    — fallback across tiers on provider-transient errors only (429/5xx/timeout), schema
    failures stay on the primary. Replaces the julep-facing half of mem-mcp's 1,137-line
    `retry_policy.py`. Depends on `Reasoner.replace()` (item 8).

19. **`julep.dispatch` primitives: debounce-by-key (signal-with-start), dedup via
    deterministic workflow id, batch-window triggers.** The dispatch boundary is rightly
    outside the IR, but consumers currently re-express debounce/dedup/batching as raw
    Temporal plumbing per pipeline (mem-mcp's RECORD quiet-period is the archetype).
    `schedule` already showed the pattern for cron; extend it.

20. **`julep keygen` + `julep dev up`.** Generating `TEMPORAL_PAYLOAD_KEYS`, deriving the
    Ed25519 signer pubkey, and sequencing temporal-dev → `serve api --migrate` →
    publish/register → worker had to be hand-rolled in mise. `keygen` printing a ready
    env block is trivial; `dev up` makes finding 11's missing operator recipe a command.

## Findings from the first EKS control-plane deployment (2026-07-27)

The rc4 control plane now runs on the existing `julep-v2-temporal-demo` EKS cluster:
two API replicas, PostgreSQL execution store, S3 release store, encrypted Temporal
payloads, digest-pinned workers, KEDA scale-to-zero, and a public ALB restricted to
the five Memory Store hosts. Three durable `grade-scores` samples completed after
release activation. These are the gaps encountered while getting there.

27. **[resolved] rc4 was not on PyPI during deployment.** PyPI now publishes
    `3.0.0rc4`; the original deployment happened while the index stopped at rc2.
    mem-mcp is moving directly to an exact rc5 source pin until rc5 is published.

28. **[fixed in deployment branch] `helm test --logs` reports a successful Job as a
    failure on Helm 3.21.** The chart creates a test Job whose Pod has a generated
    suffix. Helm's log path looks for a Pod with the unsuffixed Job name, so `julep
    apply` fails after the smoke test has actually passed. The working change removes
    `--logs` from `HelmLaneReconciler` and retains successful smoke Jobs for inspection
    (`julep/app_deploy.py`, `infra/helm/julep-worker/templates/smoke-test.yaml`). A
    better long-term shape would collect logs by the Job's label selector when the test
    fails, without making log retrieval part of pass/fail.

29. **[fixed in deployment branch] The generic worker image misses imports required by
    schema-v2 runtime preflight.** The image installed
    `julep[dotctx,temporal,store,wasm]`, but a hydrated worker traverses MCP and server
    auth imports. The deployed image adds `mcp` and `server` extras
    (`tooling/runtime-image/Dockerfile`). Add an image-level startup or smoke test that
    imports `julep.execution.bundle_worker:make_context` under the exact production
    extras, so this fails during image build rather than after a release is published.

30. **`julep status --env eks` treats an operator-network limitation as application
    failure.** Helm, Deployment, and KEDA were healthy, but the command exited 3 because
    the operator laptop cannot resolve
    `temporal-frontend.temporal.svc.cluster.local`. This is expected for a cluster-only
    Temporal endpoint. `status` should support a Kubernetes probe mode, skip direct
    Temporal probing when the address is cluster-local, or distinguish “not observable
    from here” from unhealthy. The current output marks runtime and queue state unknown,
    then returns the same nonzero class used for real drift.

31. **Release publication and activation are easy to mistake for one operation.** `julep
    apply` correctly prints `traffic unchanged`, but unpinned `POST /v1/runs` requests do
    not route to the healthy release until a separate admin `POST /v1/deployments`
    activates its lane. Explicitly release-pinned runs can use it before activation. Keep
    the separation. Improve the command's final output with the exact next command or add
    an explicit `julep activate --env <env> --lane <lane> --release <hash>` command with
    rollback symmetry.

32. **Dependency-aware readiness has no probe-safe authentication mode.** `/v1/health`
    is suitable for Kubernetes probes but does not check PostgreSQL, the artifact store,
    or Temporal. `/v1/ready` checks all three but requires a bearer token, so standard
    Kubernetes HTTP probes cannot use it without putting credentials in the Pod spec.
    Consider a loopback-only readiness endpoint, a dedicated probe token mounted from a
    Secret, or an exec-probe helper that reads the token without exposing it in the
    manifest.

33. **[fixed in deployment branch] Mixed code and configured-ctx applications pin the
    wrong worker declaration hash.** `resolve_application()` combines the imported code
    application with configured `.ctx` pipelines, then deployment passes the combined
    `compiled.runtime_declarations_hash` as `WORKER_RUNTIME_DECLARATIONS_HASH`. Worker
    startup imports only the code application's `module:attribute`, so its hash cannot
    include the config-added reasoners and it fails closed before polling. The fix hashes
    `load_application(cfg)` for worker startup while each configured `.ctx` pipeline keeps
    its release-scoped declarations blob. A mixed-application regression now covers the
    distinction (`julep/cli/application.py`,
    `tests/cli/test_application_ctx_pipeline.py`).

34. **The `yglu` extra resolves but cannot import on current setuptools.** `julep[yglu]`
    installs yglu/yaql, but yaql imports the removed `pkg_resources` module. With
    setuptools 83, `julep plan` catches that transitive `ModuleNotFoundError` and reports
    the misleading “install julep[yglu]” error even though the extra is installed. Pinning
    `setuptools>=75,<81` in the extra restores imports, with yaql's own deprecation warning.
    Longer term, upgrade or replace the yaql dependency; until then, distinguish “extra
    absent” from “installed extra failed to import” in the error message.

35. **The full test suite is invocation- and order-dependent.** `uv run pytest -q`
    fails collection because the repository root is absent from `sys.path`; `uv run
    python -m pytest -q` collects, then leaves eight failures. Several are shared
    `DEFAULT_REGISTRY` reasoner collisions that do not fail in targeted files, so an
    earlier test changes a later test's result. The remaining failures include a stale
    eval monkeypatch signature, one cross-test tool-schema expectation, and sibling
    mem-mcp prompts that now use the unsupported `skills` setting. Add the repository
    root to pytest's configured import path, isolate or restore global registries in an
    autouse fixture, and make the canonical CI command explicit in `CONTRIBUTING.md`.

## Findings from the embedded prompt pivot (2026-07-28)

36. **Embedded execution exists, but its production name is hard to find.**
    `prepare_local_pipeline(...).arun(...)` is the right boundary for a single-shot
    prompt inside a consumer-owned DBOS step. The current `local`, `dry_run`, and
    `foreground` vocabulary reads as test scaffolding, so the initial mem-mcp review
    missed it. Add a top-level "Embedded execution" page and alias namespace, and state
    the admission rule directly: use embedded Julep for prompt calls; use remote durable
    Julep when Julep replaces orchestration.

37. **The three-line embedded example assumes a Julep project config.** mem-mcp owns a
    `.ctx` package but no `julep.toml`. The supported no-file path requires importing
    `JulepConfig` and `EnvConfig` from `julep.cli.config` plus `CtxPipelineConfig` from
    `julep.ctx_pipeline`, then constructing the config object manually. These modules
    are public, but this is still control-plane vocabulary for an embedded prompt.
    `julep.embedded.load_pipeline(path, env=...)` remains a useful API: it should load a
    rich `.ctx` directory, compile one tool-less pipeline, and return `LocalPipeline`.

38. **Embedded observability is incomplete for production adoption.**
    `LocalPipeline.arun` returns only `result.value`; the in-memory projection, attempts,
    usage, cost, and artifact identity are not returned or sent to a sink. mem-mcp can
    retain its existing model-call telemetry by injecting its own `LlmCaller`, but it
    cannot get a complete Julep execution trace. Add an optional result envelope or
    projection sink without changing the value-only default.

39. **Embedded examples should show consumer-owned durability explicitly.** The DBOS
    recipe is `LocalPipeline.arun` inside the consumer's existing `@DBOS.step`. It is
    not `run_flow_dbos`, which adds a nested Julep-owned workflow around a one-model-call
    prompt. Document both shapes side by side; the distinction is the architecture
    boundary adopters need when deciding whether to use embedded or remote execution.
