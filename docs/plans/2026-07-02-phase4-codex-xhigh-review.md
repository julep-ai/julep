# Codex xhigh review — Phase 4 (Part B, Tasks 9–13) of 2026-07-01 phase 3/4 plan

> Reviewer: codex-cli 0.142.4, model_reasoning_effort=xhigh, 2026-07-02. 8 findings, ranked. Verdict: amend then ship.

[P1] Task 10 — Redaction is planned at the wrong seam  
`trajectory.py:214-231` only defines the sink/export protocol, and hydrated export reads already-persisted blobs at `trajectory.py:371-385`. The raw writes happen earlier in `execution/effects.py:531-549` and marker capture writes raw values at `execution/effects.py:621-626`; tests assert those raw canonical blobs at `tests/test_trajectory_capture.py:183-184`, `209-210`, and `276-277`.  
That fails the acceptance claim that secret-shaped input never reaches the trajectory store raw. Move redaction into `WorkerContext`/effects capture before every `blob_store.put`, with export-time redaction only as a defense-in-depth layer.

[P1] Task 9 — Prompt-cache wire shape is unsafe on the pinned Anthropic path  
The repo pins `any-llm-sdk` 1.17.0 (`uv.lock:47-49`), and CA calls `acompletion(... messages=messages, **kwargs)` from `execution/llm.py:288-324`. In that path, Anthropic system messages are string-concatenated at `.venv/.../any_llm/providers/anthropic/utils.py:115-119`, while the explicit `system: str | list[dict]` and `cache_control` API exists on `amessages` at `.venv/.../any_llm/api.py:601-617`.  
Phase 3 also preserves transcript system turns and native tool-call turns in the same builder (`/home/diwank/github.com/julep-ai/julep-v2-phase3/composable_agents/execution/llm.py:164-191`, `216-220`), so list-content system blocks can collide with multiple system messages. Amend Task 9 to use the native Anthropic/messages seam or a tested provider-specific path, and add a Phase 3 transcript/tool-call regression.

[P1] Task 13 — Queue lanes ignore an existing but inert subflow queue contract  
The public API already accepts `child.as_sub(queue="c3-q")` (`typed.py:70-75`), stores it on `SplitCapability.queue` (`typed.py:116-122`), and tests it (`tests/invariants/test_split.py:27-32`). But the serialized subflow contract has no queue field (`ir.py:283-314`), and child workflow starts omit `task_queue` (`execution/harness.py:736-753`, `2218-2233`).  
Declaring “whole-pipeline only” leaves existing queue hints silently ineffective, and mem-mcp is role-laned well beyond two lanes: foreground/maintenance/summary/slack/brief-refresh/record-quality/record-execute appear in `docker-compose.unified-production.yml:304-390`, `455-505`, and `580-688`. Either explicitly deprecate/remove subflow queues or implement serialized per-subflow lane resolution and map the real mem-mcp roles.

[P2] Task 9 — Cache fallback observability is missing  
`LlmCallMeta` records provider/model, usage, attempts, cost, response-format fallback, and retries, but no prompt-cache requested/applied/read/create fields (`execution/llm_result.py:23-61`). The mem-mcp reference says prompt-cache markers must “never be silently dropped” and ties that to the `$11k-13k/mo` cost risk (`utils/model_override.py:1-7`, `32-40`, `76-82`).  
A non-Anthropic “inert” setting or any provider fallback would be invisible today. Amend Task 9 to record `prompt_cache.requested`, `applied`, `reason`, `cache_read_tokens`, and `cache_creation_tokens` on `LlmCallMeta`, or fail loudly unless inert behavior is explicitly opted in.

[P2] Task 12 — Schedule execution shape bypasses deployed-run invariants  
Current remote `ca run` reads the deploy ledger and calls `run_flow` with `flow_json`, `manifest_json`, `task_queue`, `bundle`, and `pinned_pures` (`ca/temporal_run.py:44-65`). The helper builds a full `FlowInput` with policy/principal/root/bundle fields and starts `FlowWorkflow.run` on the task queue (`execution/harness.py:2354-2394`).  
A plan that says `ScheduleActionStartWorkflow(FlowWorkflow, args=[frozen artifact input...])` is too loose and risks schedules that do not replay the deployed artifact or pure-hash pins. Define a shared schedule payload builder around `FlowInput`/ledger records, including bundle and pinned pures, before adding `ca schedule`.

[P2] Task 11 — Versioning is aimed at a nonexistent entrypoint and misses serve env wiring  
The actual worker seams are `build_worker(..., **worker_kwargs)` and `run_worker(..., **worker_kwargs)`, already passing kwargs through to Temporal `Worker` (`execution/worker.py:138-195`, `198-242`). The process env entrypoint is `execution/serve.py`, whose settings/env parser has no build-id or versioning fields (`execution/serve.py:82-133`) and only passes shutdown/concurrency kwargs (`execution/serve.py:291-302`).  
Adding `start_worker(... build_id, use_worker_versioning)` would be duplicate or dead unless serve is wired. Amend Task 11 to add `JULEP_WORKER_BUILD_ID`/`JULEP_WORKER_VERSIONING` to `WorkerServeSettings` and pass them through existing `build_worker`.

[P2] Task 10 — The default redactor does not close the PII precondition  
The cited heuristic is key-name only: `SECRET_KEY_RE` matches `token|secret|password|api_key|credential|private_key` (`validate.py:59-63`) and is currently used to reject static ARR argument keys, not arbitrary runtime values (`validate.py:315-327`). Trajectory capture stores arbitrary `input_value`/`output_value` blobs, so PII in fields like memory text, brief content, or user background will not match this default.  
Keep the heuristic for secrets, but make Phase 4 acceptance require a mem-mcp-specific runtime redactor with fixture tests for real memory/checkin/brief payload shapes before migration.

[P3] Task 11 — Replay corpus scope is narrower than the registered worker surface  
The worker registers six workflows: `FlowWorkflow`, `SessionWorkflow`, `AgentWorkflow`, `DebounceCollector`, `BatchCollector`, and `BatchPoll` (`execution/worker.py:106-113`). The plan’s replay corpus names only Flow/Agent/Session, so future changes in debounce/batch workflow code would not be replay-gated even though those workflows ship in the same worker.  
Either expand the corpus/replayer list to all registered workflows or state that Phase 4’s replay gate covers only agent-loop histories and add a separate gate for batching workflow histories.

Overall verdict: amend then ship. The biggest risk is that Task 9 and Task 10 currently validate the production preconditions at the wrong seams: prompt caching can be silently absent, and redaction can happen after raw sensitive data is already durable.


