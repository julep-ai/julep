# mem-mcp Adoption Phase 3/4: Agent-Loop Parity + Production Pre-conditions

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task, TDD, commit after each task with prefix `feat(phase3):` / `fix(phase3):` / `feat(phase4):`.

**Goal:** Part A (Phase 3) makes the agent loop able to faithfully run mem-mcp's 6 tool-calling agents: native provider tool-calling with parallel calls, tool-error observations instead of run aborts, session turn survival, `require_tool_call` enforcement, per-round dynamic context, and an eval runner that replays mem-mcp's 23 eval suites as the acceptance gate. Part B (Phase 4) closes the four production pre-conditions no earlier phase covers: Anthropic prompt caching, trajectory redaction, Temporal replay-versioning discipline, and cron/queue-lane primitives.

**Architecture:** Phase 3 changes concentrate in the pure loop core (`agent_loop.py`, `turn.py`, `transcript.py`), the provider seam (`execution/llm.py`, `execution/llm_result.py`), and the facade (`agent.py`); every new loop behavior is a pure, JSON-serializable state/config change so all four backends (local/DBOS/Temporal/CMA) inherit it. Native tool-calling is a passthrough: any-llm's `acompletion` already accepts `tools`/`tool_choice`/`parallel_tool_calls` and returns `message.tool_calls`; we add the wiring, the decision vocabulary, and the transcript round-trip. Phase 4 sits in `execution/llm.py` (provider-safe prompt-cache markers behind an `_apply_prompt_cache` seam), `execution/effects.py` + `trajectory.py` (redaction at the capture seam, export as defense-in-depth), `execution/serve.py` + a new replay-corpus test harness covering all six registered workflows (versioning), and `ca` + `ir.py`/`harness.py` (schedules on a shared start-args builder + per-subflow queue lanes).

**Tech Stack:** Python 3.10+, any-llm (`tools=`, `tool_calls`, `parallel_tool_calls` already in its signature), Temporal (`temporalio.worker` Build IDs, `WorkflowReplayer`, Schedule API), pytest, mypy --strict, ruff.

## Global Constraints

- Gates: `python -m pytest` (never bare pytest), `uv run mypy --strict composable_agents` (package only), `ruff check composable_agents tests`.
- New tests must not require temporal unless `@skipif(not HAVE_TEMPORAL)`-guarded (the temporal=off CI job must stay green).
- Existing deploy goldens byte-for-byte unchanged: every new identity field enters `deploy.py:_reasoner_identity` omit-when-unset, matching the existing convention.
- G-8: no silent fallbacks — provider fallbacks are recorded on `LlmCallMeta`; unsupported values are loud teaching errors.
- `AgentState`/`TraceEntry` JSON changes must be additive with `from_json` defaults (continue-as-new state from live runs must keep loading); bump `STATE_SCHEMA_VERSION` only if a field is *reinterpreted*, never for additions.
- New `LlmCallMeta.to_attrs()` keys emitted only when non-default (projection/Langfuse attr snapshots unchanged).
- Behavior flags default OFF (`native_tools=False`, `prompt_cache=None`, redaction default = scrub) so existing users and goldens are unaffected; the mem-mcp port opts in.
- Commit after every task.

## Reference: mem-mcp semantics being mirrored (Phase 3)

- Tool-loop driver: pydantic-ai native tool-calling (`dotctx/integrations/pydantic_ai.py:531,609`), bounded by `UsageLimits(request_limit=max_rounds)`.
- Tool-only mode (`require_tool_call: true`, 5 prompts): runs `.iter()`, synthesizes empty output when the model never produces final text — "success = tool side-effects happened" (`pydantic_ai.py:352`).
- Tools defensively return `{"error": str(e)}` dicts and the model retries (e.g. `agent_loops/thread_merge.py:187-189`); the loop never dies on a tool exception.
- Per-round dynamic context: record_execute appends "[REMAINING ROUNDS: N]" each round (`agent_loops/record_agents.py:103`) — a pure function of loop state.
- Eval surface: `sample(limit)` / `score(input, output, expected)` modules + `eval.yaml` (models/datasets/threshold/concurrency/scoring/profiles) — loading shipped in Phase 2 (`dotctx_evals.py`); this phase adds the *runner* and the regression diff (mem-mcp's `tooling/scripts/eval/eval_diff.py`, CI gate `prompt-eval-smoke`).
- Prompt caching: mem-mcp stamps Anthropic 1h `cache_control` markers on every Anthropic call (`utils/model_override.py:37`); worth ~$11–13k/mo. Migrating without parity is a hard cost regression.

---

# Part A — Phase 3: agent-loop parity

### Task 1: Tool errors become observations, never run aborts

**Files:**
- Modify: `composable_agents/agent_loop.py:219-253` (`TraceEntry`), `composable_agents/turn.py:164-183` (the CALL branch)
- Modify: `composable_agents/agent.py:811-819` (facade `call_tool` — keep, now redundant defense)
- Test: `tests/test_tool_error_observation.py`

**Interfaces:**
- Produces: `TraceEntry(error: Optional[str] = None)` (+ `"error"` key in `to_json`/`from_json`, omit-when-unset); `controller_turn` catches tool/subflow exceptions and folds them into the observation.

Behavior:
- In `turn.py`'s CALL branch, wrap `out = await call_tool(tool, call_input)` in try/except. On exception: `out = {"error": repr(exc), "tool": tool}`, log a warning on the `composable_agents.turn` logger, record `TraceEntry(decision="call", ref=tool, cost=cost, error=repr(exc))`, set `state.last = out`, increment the round, and continue — the model sees the error next round and can retry or escalate. Identical treatment for the SUB branch (`run_subflow`).
- The catch sits in `controller_turn` (not per-backend `call_tool` closures) so local, DBOS, and Temporal all inherit it: on Temporal, the activity's own RetryPolicy runs first; only after retries exhaust does the raised `ActivityError` become an observation instead of a workflow failure.
- Denials (`authorize_call`, `maxCalls`) are unchanged — policy refusals still Halt; only *execution* failures become observations.
- Termination stays bounded by the existing guards: `max_rounds`, budget, and per-tool `maxCalls` (a tool that always throws still counts against `maxCalls` because `charge_tool_call` runs before invocation).
- `AgentState.from_json` must load pre-change trace entries (no `error` key) — additive only, no `STATE_SCHEMA_VERSION` bump.

Tests: raising sync tool → status `done` (model finishes after seeing the error), trace entry carries `error` and `state.last` was the error dict on the intermediate round; raising async tool same; raising subflow same; `to_json` omits `error` when None and round-trips when set; old-format trace JSON loads; denial still Halts with `denied`; scripted controller that retries the tool after seeing `{"error": ...}` succeeds on second call.

- [ ] Write failing tests → implement → `python -m pytest tests/test_tool_error_observation.py -v` → full gates → commit `fix(phase3): tool/subflow exceptions become observations, not run aborts`

### Task 2: Session turns survive non-fatal errors

**Files:**
- Modify: `composable_agents/session.py:1020-1055` (driver loop)
- Test: `tests/test_session_error_survival.py` (extend existing session test module conventions)

**Interfaces:**
- Produces: per-turn `except Exception` handling inside the `for` loop — non-fatal `SessionEvent.error(reason, fatal=False)` + continue; new `LocalSessionHandle` config knob `max_consecutive_turn_errors: int = 3` (constructor keyword, threaded from `@session`/`chat` entry points with the same default).

Behavior:
- Move the generic `except Exception` from around the whole `for` loop (session.py:1046) to *inside* it, alongside the existing `SessionTurnError(fatal=False)` arm: any exception during one turn's `interpret` emits a non-fatal error event and continues to the next message. `SessionClosed` and `SessionTurnError(fatal=True)` keep their current semantics (break / tear down).
- A consecutive-error counter (reset on any successful turn) tears the session down with a fatal event after `max_consecutive_turn_errors` back-to-back failures — a poisoned carrier must not spin forever.
- The outer try/finally keeps handling setup errors (missing LOOP body) and the close path exactly as today.

Tests: turn 2 of 4 raises → error event (fatal=False) observed, turns 3–4 still process, session closes cleanly; 3 consecutive raises → fatal error event + closed; counter resets after a good turn (raise, ok, raise, ok → session alive); `SessionClosed` still exits silently; fatal `SessionTurnError` still tears down immediately.

- [ ] TDD → gates → commit `fix(phase3): session turns survive non-fatal errors with a consecutive-error bound`

### Task 3: Native tool-calling in the provider seam

**Files:**
- Modify: `composable_agents/execution/llm.py:257-369` (`complete_reasoner`), `composable_agents/execution/llm_result.py`
- Test: `tests/test_llm_native_tools.py`

**Interfaces:**
- Produces: `complete_reasoner(..., tools: Optional[list[dict[str, Any]]] = None, parallel_tool_calls: Optional[bool] = None)`; both seam factories (`make_llm_caller`, `make_resilient_llm_caller`) grow the same passthrough kwargs on their `caller(...)` signatures (keyword-only, default None). When the completion carries `message.tool_calls`, the returned `LlmResult.reply` is `{"tool_calls": [{"id": <call id>, "tool": <fn name>, "input": <parsed args>}...]}`; otherwise behavior is unchanged. `LlmCallMeta.native_tool_calls: int = 0` (attr `"llm.tool_calls"` only when > 0).

Behavior:
- When `tools` is non-empty: pass `tools=tools` (and `parallel_tool_calls` when not None) to `acompletion`; do NOT send `response_format` in the same request (the reply schema describes the *finish* payload, which now arrives as plain text/JSON when the model doesn't call tools) — the schema stays prompt-injected via `schema_hint` so FINISH replies still parse. This sidesteps the native/`response_format` latch entirely on tool rounds.
- Tool-call args arrive as JSON strings (`tool_call.function.arguments`): parse tolerantly (`json.loads`, fall back to raw string on decode error — the loop will surface it to the model as a malformed-input tool error via Task 1).
- Empty `tools` / None → exactly today's path, byte-for-byte (goldens + existing llm tests unchanged).
- Providers in `_PROMPT_FALLBACK_PROVIDERS` still get `tools=` (the fallback set is about `response_format` conversion, not tool support); a provider error on a tools request is NOT downgraded — it propagates to the resilient caller's ladder like any other call failure (classify + retry/advance).

Tests (fake `acompletion` capturing kwargs): `tools` and `parallel_tool_calls` forwarded verbatim; completion with two `tool_calls` → reply is the normalized dict with parsed args; string-args decode failure → raw string kept as `input`; no `tool_calls` + schema → current parse path (dict reply); `tools=None` sends no `tools` kwarg; `response_format` absent when tools are sent, `schema_hint` block present in system; meta counts `native_tool_calls` and `to_attrs` emits only when > 0.

- [ ] TDD → gates (include `tests/test_llm.py tests/test_resilient_llm.py` for regressions) → commit `feat(phase3): native tools= passthrough + tool_calls reply normalization`

### Task 4: The loop speaks tool_calls — multi-call rounds

**Files:**
- Modify: `composable_agents/agent_loop.py:56-138` (`Decision`, `interpret_reasoner_reply`, `action_cost`), `composable_agents/turn.py:101-202` (`controller_turn`), `composable_agents/agent_loop.py:151-216` (`AgentConfig.native_tools: bool = False`, in `from_json`/`to_json` as `"nativeTools"`, omit-when-false)
- Modify: `composable_agents/agent.py` (facade: build provider tool defs from `self._tools` and thread them + `cfg.native_tools` into `invoke_controller` payloads — the payload gains `"tools"`: the provider-format list — and the llm seam consumes it; `make_local_reasoner` forwards `payload["tools"]`)
- Test: `tests/test_agent_native_tools.py`

**Interfaces:**
- Consumes: Task 3's `{"tool_calls": [...]}` reply shape and `tools=` seam.
- Produces: `Decision.CALL_MANY = "call_many"` with payload `list[{"id","tool","input"}]`; `provider_tool_defs(tools: Sequence[Tool]) -> list[dict]` in `agent.py` — `{"type": "function", "function": {"name": t.name, "description": (t.fn.__doc__ or "").strip(), "parameters": t.input_schema}}`.

Behavior:
- `interpret_reasoner_reply`: a dict reply with a non-empty `"tool_calls"` list → `RoundAction(Decision.CALL_MANY, [...])` (each entry validated to have a string `tool`; malformed entries → CONTROLLER_ERROR in strict mode). A single-entry list still uses CALL_MANY (uniform trace shape).
- `controller_turn` CALL_MANY branch: authorize **every** call first (any denial → the whole round's existing denial handling: STRICT halts, DEV warns-and-allows); charge `maxCalls` per call; then execute — calls whose carried contract effect is `READ` (via `contract_for_tool`) run concurrently with `asyncio.gather`, everything else strictly in list order after the reads (same fencing rule as `dag.py`'s effect layers). Each call records its own `TraceEntry(decision="call", ref=tool, error=...)` with a new optional `call_id` field (additive JSON, like Task 1). `state.last` becomes `[{"id": ..., "tool": ..., "output": ...}, ...]` in the model's emission order.
- Round accounting: one round per CALL_MANY (matches provider semantics — parallel calls are one assistant turn); cost = `DEFAULT_TOOL_COST * len(calls)` through `action_cost` (extend it for CALL_MANY); budget precheck uses that total.
- When `cfg.native_tools` is False nothing changes: the reply schema remains `AGENT_REPLY_SCHEMA`, `tools` are not sent, and `tool_calls` replies are treated as today (malformed → controller_error in strict mode). The flag is carried through `AgentConfig.to_json`/`from_json` so the Temporal `AgentWorkflow` (which reconstructs cfg from JSON) inherits the behavior with zero harness changes beyond payload threading.

Tests: two-call reply → both executed, two trace entries with `call_id`s, one round consumed, `state.last` ordered per emission; READ+READ pair runs concurrently (assert via started/finished event ordering with async fakes); READ+WRITE runs write after read; denial on second call halts round in STRICT; failing call → error observation for that entry only, sibling result intact (composes with Task 1); `native_tools=False` + `tool_calls` reply → controller_error; cfg JSON round-trips `nativeTools` omit-when-false; `provider_tool_defs` emits name/description/parameters from a real `@tool`.

- [ ] TDD → gates → commit `feat(phase3): CALL_MANY rounds — native parallel tool calls with effect-fenced execution`

### Task 5: Transcript round-trips native tool calls

**Files:**
- Modify: `composable_agents/transcript.py:26-45` (`Turn`), the transcript-building sites that record call/result turns, and `composable_agents/execution/llm.py:145-169` (`_transcript_messages`)
- Test: `tests/test_transcript_native_tools.py`

**Interfaces:**
- Produces: `Turn` gains optional `tool_call_id: str` and assistant turns gain optional `tool_calls: list[dict]` (provider-format); `_transcript_messages` emits `{"role": "assistant", "tool_calls": [...]}` followed by `{"role": "tool", "tool_call_id": ..., "content": ...}` whenever ids are present.

Behavior:
- When the loop runs `native_tools`, the WHOLE_SESSION/SUMMARY transcript records the assistant's tool_calls turn verbatim (ids included) and each tool result as a `tool`-role turn keyed by `tool_call_id`, so the *next* round's provider messages replay the exchange in the provider's own grammar (required by OpenAI/Anthropic for multi-round tool use).
- Turns without ids keep today's text mapping exactly (`[called X]` / `[X result]` prefixes) — replayed pre-change transcripts and non-native runs are unchanged.
- SUMMARY-scope elision treats an assistant-tool_calls turn + its tool results as one elidable unit (never orphan a `tool` turn whose call id was summarized away — providers reject that).

Tests: native turn pair renders assistant `tool_calls` + `tool` role messages with matching ids; id-less turns render exactly as before (golden equality against current output); mixed transcript ordering preserved; summary elision drops call+results atomically.

- [ ] TDD → gates → commit `feat(phase3): transcript carries tool_call ids; provider-native replay grammar`

### Task 6: `require_tool_call` enforcement (tool-only mode)

**Files:**
- Modify: `composable_agents/turn.py` (`controller_turn`), `composable_agents/agent_loop.py` (`AgentConfig.require_tool_call: bool = False`, JSON key `"requireToolCall"`, omit-when-false), `composable_agents/agent.py` (thread from `Reasoner.require_tool_call` — the Phase 2 field — when the facade builds `AgentConfig`)
- Test: `tests/test_require_tool_call.py`

**Interfaces:**
- Consumes: `Reasoner.require_tool_call` (Phase 2), Task 1's error-observation convention.
- Produces: loop semantics — FINISH is only accepted after ≥1 successful tool call this run; premature text gets a bounded re-ask.

Behavior (mirrors mem-mcp `pydantic_ai.py:352`):
- With `cfg.require_tool_call` and zero successful CALL/CALL_MANY trace entries so far: a FINISH decision does not halt; instead the loop re-asks — `state.last` becomes `{"error": "require_tool_call: reply with a tool call, not text", "reply": <the text>}`, a `TraceEntry(decision="reask", error=...)` is recorded, the round increments, and the controller runs again. Bounded by a fixed 2 re-asks (counted via trace `reask` entries), after which the run halts `controller_error` with reason `"require_tool_call: controller never called a tool"`.
- Once any tool call has succeeded, FINISH behaves normally — and a controller that goes silent (max_rounds reached after tool calls) terminates `max_rounds` with `output=None`, which the facade maps to a successful empty output when `require_tool_call` is set ("success = side-effects happened"): `terminal_result` status stays truthful; the *facade* `Result` treats `max_rounds`+`require_tool_call`+≥1 call as ok.
- ESCALATE and CONTROLLER_ERROR are never suppressed.

Tests: text-first reply → re-ask observed, tool call on round 2 → done; three text replies → controller_error with the teaching reason; tool call then FINISH → normal done; tool call then silence to max_rounds → facade Result ok with output None; flag absent → today's behavior byte-for-byte; cfg JSON round-trip.

- [ ] TDD → gates → commit `feat(phase3): require_tool_call loop enforcement with bounded re-ask`

### Task 7: Per-round dynamic context (registered-pure round notes)

**Files:**
- Modify: `composable_agents/agent_loop.py` (`AgentConfig.round_note: Optional[str] = None`, JSON `"roundNote"`), `composable_agents/turn.py` (`controller_turn` payload), `composable_agents/std.py` (new std pure)
- Test: `tests/test_round_note.py`

**Interfaces:**
- Produces: `cfg.round_note` names a registered pure `(ctx: dict) -> Optional[str]` where `ctx = {"round": state.round, "maxRounds": cfg.max_rounds, "spent": state.spent, "callCounts": {...}}`; when it returns a string, the controller payload gains `"note": <string>` (rendered by the prompt path as a trailing system line). New std pure `std.rounds_remaining_note` returning `f"[REMAINING ROUNDS: {maxRounds - round}]"`.

Behavior:
- Resolved through the same pure registry as `arr` nodes (deploy-time `UNKNOWN_PURE` validation applies — an unregistered name is a blocking diagnostic in `validate.py`, and `deploy.py` pins its hash like any other pure). Being a registered pure keeps the note deterministic under Temporal replay and identical across backends.
- Computed fresh every round from the ctx dict only — it never sees `state.last` or the transcript (no covert channel into the deterministic path).
- mem-mcp port note (doc comment): `record/execute.ctx`'s "[REMAINING ROUNDS: N]" maps to `round_note="std.rounds_remaining_note"`.

Tests: scripted controller asserts payload `note` present each round with decremented count; None-returning pure → no `note` key; unregistered name → deploy-time diagnostic (extend the existing validate test conventions); std pure output exact; JSON round-trip omit-when-unset.

- [ ] TDD → gates → commit `feat(phase3): round_note registered pure — per-round dynamic controller context`

### Task 8: Eval runner — `ca eval` + regression diff

**Files:**
- Create: `composable_agents/ca/evalrun.py`; Modify: `composable_agents/ca/cli.py` (new `eval` command)
- Test: `tests/ca/test_eval_cli.py`

**Interfaces:**
- Consumes: Phase 2's `dotctx_evals.load_ctx_evals(ctx_dir, env=)` (`EvalModule.sample/score`, `EvalConfig` incl. `threshold`/`concurrency`/`models`, `MockToolConfig`).
- Produces: `ca eval <path/to/name.ctx> [--env local] [--limit N] [--json out.json] [--baseline old.json]`; report shape `{"ctx": str, "model": str, "samples": int, "scores": [{"id", "score", "passed"}...], "mean": float, "threshold": float, "passed": bool}`; exit 0 pass, 2 below threshold, 3 regression vs `--baseline` (any sample passed→failed or mean drop > 0.01).

Behavior:
- For each sample from `sample(limit)`: build the run — single-shot reasoners go through `complete_reasoner` (resolved acompletion, env-profile model); tool-loop agents (`tools.pyi` present) run `drive_agent_loop` with `native_tools=True` and tools stubbed from the sample's `MockToolConfig` (mock outputs keyed by tool name; unmocked tool call → recorded error observation via Task 1, surfaces in the score). Stop conditions honor the ported `StopFn`s (`stop_after_turns` → `max_rounds` override, `stop_when_terminal_tool` → halt after that tool's trace entry).
- `score(input, output, expected)` runs in-process (it's user code — same trust stance as `load_eval_module`, CLI-time only); scores aggregate to mean vs `EvalConfig.threshold`; `concurrency` bounds sample parallelism via `asyncio.Semaphore`.
- `--baseline` implements the eval_diff contract (mem-mcp `tooling/scripts/eval/eval_diff.py`): compare per-sample pass sets and means, exit 3 with a table of regressed samples. This is the CI gate replacement for `prompt-eval-smoke`.
- No live-provider requirement in tests: inject a fake acompletion through the same seam the llm tests use.

Tests: fixture `.ctx` + eval.py (from Phase 2's `tests/fixtures/memmcp/`) runs end-to-end with a scripted acompletion → report JSON shape exact, threshold pass/fail exit codes; mock-tool agent sample runs the loop and scores trace-derived output; `--baseline` regression → exit 3 naming the sample; concurrency respected (max in-flight assertion); unmocked tool call becomes a scored failure, not a crash.

- [ ] TDD → gates → commit `feat(phase3): ca eval — sample/score runner with threshold + baseline regression gate`

---

# Part B — Phase 4: production pre-conditions

> **Amended 2026-07-03** per the codex@xhigh review (`docs/plans/2026-07-02-phase4-codex-xhigh-review.md`, 8 findings, verdict "amend then ship"). Every finding is folded into the task it targets; the two P1 seam errors (Task 9 wire shape, Task 10 redaction seam) reshape those tasks' interfaces.

### Task 9: Anthropic prompt caching (`cache_control`)

**Files:**
- Modify: `composable_agents/dotctx.py` (`Reasoner.prompt_cache: Optional[str] = None`, settings key `prompt_cache` accepting `"5m"|"1h"`, teaching error otherwise), `composable_agents/dotctx_rich.py` (`_ALLOWED_SETTINGS`), `composable_agents/deploy.py:_reasoner_identity` (`"promptCache"` omit-when-unset), `composable_agents/execution/llm.py` (`_apply_prompt_cache` hook + `call` closure), `composable_agents/execution/llm_result.py` (cache request + usage fields)
- Test: `tests/test_llm_prompt_cache.py`

**Interfaces:**
- Produces: `_apply_prompt_cache(provider, prompt_cache, messages, kwargs) -> tuple[messages, kwargs]` — a single seam in `execution/llm.py` where the provider-specific cache wiring lives; tests assert on the messages/kwargs it actually emits, so the wire detail stays behind the seam. For anthropic the *intent* is two markers — stable prefix (system) + growing conversation (last transcript turn), `ttl: "1h"` present / `"5m"` bare — but the exact wire shape is decided by the spike (below), NOT assumed. `LlmCallMeta` gains `prompt_cache_requested: str | None`, `prompt_cache_applied: bool | None`, `prompt_cache_reason: str | None`, `cache_read_tokens: int | None`, `cache_creation_tokens: int | None` (usage keys: `prompt_tokens_details` / anthropic-style `cache_read_input_tokens` / `cache_creation_input_tokens`); attrs `"llm.cache"` dict, omit-when-absent.

Behavior:
- **[P1 amendment] The naive list-content system rewrite is known-unsafe on the anthropic completion path**: any-llm's anthropic completion adapter string-concatenates system messages (observed at 1.17.0 `providers/anthropic/utils.py:115-119`; the worktree now carries **1.19.0** — the spike's first step is re-verifying the installed version's adapter before choosing a path), so a `{"role": "system", "content": [blocks]}` message may be flattened or corrupted. The spike (gating step 0, before any TDD) decides between the two viable paths and records the answer in the test file's module docstring: (a) thread `cache_control` via provider kwargs/`extra_body` through `acompletion`, or (b) route anthropic+prompt_cache calls through any-llm's `amessages` API (`api.py:601-617`), which has explicit `system: str | list[dict]` + `cache_control` support. Acceptance for the spike: one live anthropic call shows `cache_creation_input_tokens > 0`, a second shows `cache_read_input_tokens > 0` (keys from `.env`; `@pytest.mark.live`, excluded from CI).
- **[P1 amendment] Phase 3 collision regression**: the same message builder now carries transcript system turns and native tool-call turns (`execution/llm.py` transcript path). A regression test drives `prompt_cache` + a transcript containing system turns and provider tool-call/tool-result turns through `_apply_prompt_cache` and asserts no message shape is corrupted and markers land only where intended.
- **[P2 amendment] Inert is allowed but never invisible**: a `prompt_cache` value on a non-anthropic model stays inert on the wire (OpenAI-side caching is automatic) but is *recorded* — `prompt_cache_requested="1h"`, `prompt_cache_applied=False`, `prompt_cache_reason="provider_inert"` on `LlmCallMeta`; same recording when a resilience-ladder fallback crosses from anthropic to a non-anthropic provider mid-call (`prompt_cache_reason="fallback_provider"`). This closes the "silently dropped cache markers" risk the mem-mcp reference ties to the $11–13k/mo cost line (G-8).
- `_messages` keeps returning plain-string content when `prompt_cache` is unset — every existing test and golden is untouched.

Tests: anthropic + `prompt_cache="1h"` → spike-decided wire shape with ttl, last transcript turn marked; `"5m"` → no ttl key; unset → plain strings (golden equality); openai + set → wire untouched but meta records requested/applied=False/reason; fallback-crossing-provider records reason; settings loader accepts/validates values, identity omits-when-unset (deploy goldens unchanged); meta cache fields from a fake usage payload; `to_attrs` omission rules; the Phase 3 transcript/tool-call collision regression.

- [ ] Spike (live, keys from `.env`, decides wire path) → TDD → gates → commit `feat(phase4): anthropic prompt_cache — provider-safe cache markers + cache observability meta`

### Task 10: Trajectory redaction (PII/secrets never land raw)

**Files:**
- Modify: `composable_agents/execution/effects.py` (**[P1 amendment] the actual write seams**: trajectory capture before every `blob_store.put` — both the tool/reasoner input/output capture path (~`:531-549`) and the marker capture path (~`:621-626`)), `composable_agents/execution/effects.py:WorkerContext` (redactor injection for durable backends), `composable_agents/trajectory.py` (local `TrajectoryRecorder` write path + export defense-in-depth), reuse the secret-key heuristic from `composable_agents/validate.py:61` (extract to a shared helper if it isn't importable cleanly)
- Modify: `tests/test_trajectory_capture.py` — the assertions that pin raw canonical blobs (~`:183-184`, `:209-210`, `:276-277`) are updated deliberately in the same commit: raw-equality asserts survive only for non-secret-shaped payloads; secret-shaped fixtures assert the redacted form
- Test: `tests/test_trajectory_redaction.py`

**Interfaces:**
- Produces: `Redactor = Callable[[Any], Any]`; injectable at BOTH seams — `TrajectoryRecorder(..., redactor: Optional[Redactor] = None)` for the local recorder and `WorkerContext(..., redactor: Optional[Redactor] = None)` for durable-backend capture. When None, the default `redact_secret_shaped(value)` applies: any dict key matching the shared secret-key pattern has its value replaced by `"[REDACTED]"`, recursively. The pattern is validate.py's `SECRET_KEY_RE` (`token|secret|password|api_?key|credential|private_?key`, case-insensitive) extended with `authorization|bearer` for the redaction helper (bare `key` is deliberately NOT matched — `cache_key`/`primary_key` false positives); extending rather than mutating `SECRET_KEY_RE` keeps the ARR validation behavior untouched. `export_trajectory_jsonl_hydrated(..., redactor: Optional[Redactor] = None, allow_raw: bool = False)` — hydrated values pass through the redactor as defense-in-depth; `allow_raw=True` is the only way to skip it, and it logs a warning naming the export path.

Behavior:
- **[P1 amendment] Redaction happens at the *capture* seam, before every `blob_store.put`** — in `execution/effects.py` where the raw writes actually occur (input/output capture AND marker capture), not only in `trajectory.py`, whose export path reads blobs that are already durable. The trajectory store never contains the raw secret, so no later export path can leak it; export-time redaction is retained as a second layer, not the primary defense. Projection/observability planes are NOT touched (they are ref-based and per-run; scope creep here breaks the Langfuse attr snapshots).
- **[P2 amendment] The default heuristic is a secrets floor, not a PII close**: key-name matching cannot catch PII inside values (memory text, brief content, user background). The injectable seam is the deliverable; the acceptance test proves it carries real weight — a fixture value-level redactor is driven over mem-mcp-shaped payloads (a memory-record dict with free-text `content`, a checkin payload, a brief body) and the stored blobs show the fixture redactor's output. The production mem-mcp redactor itself lives in the mem-mcp repo; this task ships the seam + the shape-proof. Document the mem-mcp expectation (hash-pointer redactor) in the module docstring.
- Best-effort discipline preserved: a raising redactor counts a `_BEST_EFFORT_FAILURES` and drops the record (fail-closed — a broken redactor must not default to writing raw).

Tests: tool input `{"api_key": "sk-...", "q": "hi"}` captured (effects seam) → stored blob has `[REDACTED]` + intact `q`; same via local `TrajectoryRecorder`; marker-capture path redacts too; nested dicts/lists recurse; custom redactor replaces default at both seams; mem-mcp-shaped payload fixtures through a value-level fixture redactor; export without `allow_raw` applies redactor to hydrated blobs; `allow_raw=True` warns; raising redactor drops the record and increments the failure counter (nothing raw persisted); updated `test_trajectory_capture.py` raw asserts hold for non-secret payloads.

- [ ] TDD → gates → commit `feat(phase4): trajectory redaction at the capture seam — secret-shaped scrub by default, fail-closed`

### Task 11: Temporal replay-versioning discipline

**Files:**
- Modify: `composable_agents/execution/serve.py` (**[P2 amendment] the real env entrypoint**: `WorkerServeSettings` + env parser + the `build_worker(...)` call site), `CONTRIBUTING.md` (policy section) — `execution/worker.py` needs NO new function: `build_worker`/`run_worker` already pass `**worker_kwargs` straight through to `temporalio.worker.Worker` (`worker.py:138-195`, `198-242`)
- Create: `tests/replay/test_replay_corpus.py`, `tests/replay/histories/` (recorded histories), `tests/replay/record_histories.py` (regeneration script)
- Test: the corpus test itself (guarded `@skipif(not HAVE_TEMPORAL)`)

**Interfaces:**
- Produces: **[P2 amendment]** `WorkerServeSettings` gains `build_id: Optional[str] = None` / `use_worker_versioning: bool = False`, parsed from `CA_WORKER_BUILD_ID` / `CA_WORKER_VERSIONING=1`; when versioning is on and no build_id is given, it defaults to the package version (`importlib.metadata.version("composable-agents")`); serve threads both into the existing `build_worker(..., **worker_kwargs)` seam as `build_id=...`, `use_worker_versioning=True`. There is no new `start_worker` — the plan previously named a nonexistent entrypoint.

Behavior:
- **The corpus is the gate.** `record_histories.py` runs the existing time-skipping e2e scenarios against the *current* code and saves `WorkflowHistory` JSON per scenario. **[P3 amendment] The corpus covers the full registered worker surface** — all six workflows registered in `worker.py:106-113`: `FlowWorkflow` (par/each/sub), `AgentWorkflow` (loop with continue-as-new), `SessionWorkflow` (store), `DebounceCollector`, `BatchCollector`, `BatchPoll` (one recorded scenario each, reusing the existing batching e2e fixtures). `test_replay_corpus.py` replays every stored history through `temporalio.worker.Replayer(workflows=[<all six>])` — any nondeterministic change to the interpreter/harness (cid allocation, par scheduling, new commands) fails this test *before* it ships, which is exactly the failure mode M8 identified (only 3 `workflow.patched()` gates exist today, `harness.py:283-300`, all bundle plumbing).
- Policy (CONTRIBUTING): a corpus failure means the change must either be gated behind `workflow.patched("<ticket>")` (and the corpus re-recorded once the deprecation window closes) or shipped under a new Build ID with worker versioning on. Corpus histories are only regenerated in the same PR that adds a patched-gate or bumps the versioning story — never to "fix the test".
- Build-ID wiring is opt-in because it changes task-queue semantics (versioned queues need Temporal server support); the helm chart gains the two env vars, default off.
- **Deliberate deprecation note**: temporalio 1.30 (installed) marks `build_id`/`use_worker_versioning` deprecated in favor of `deployment_config`. We use the deprecated kwargs anyway — the stable contract we ship is the `CA_WORKER_*` env seam; the underlying Worker kwarg can swap to `deployment_config` later without touching that contract. Say so in a code comment at the `build_worker` call site and filter/acknowledge the deprecation warning in the test.

Tests: corpus replays clean at HEAD for all six workflows; a deliberate scheduling mutation (test-local monkeypatch reordering a gather) makes the replayer raise (proves the gate has teeth); serve settings parse the two env vars and the `build_worker` call captures `build_id`/`use_worker_versioning` kwargs (fake Worker capture); defaults byte-identical to today (no kwargs passed when unset).

- [ ] Record corpus → TDD → gates (temporal job) → commit `feat(phase4): replay corpus gate + opt-in worker Build-ID versioning`

### Task 12: Cron schedules — `ca schedule`

**Files:**
- Modify: `composable_agents/ca/config.py` (`[schedule.<name>]` tables), `composable_agents/ca/cli.py`
- Create: `composable_agents/ca/schedule.py`
- Test: `tests/ca/test_schedule.py`

**Interfaces:**
- Produces: `ScheduleConfig(name, cron: str, flow: str, input: Any = None, env: str = "local", paused: bool = False)` parsed from ca.toml (`[schedule.hourly-rollup] cron="0 * * * *" flow="rollups.hourly" input={...}`); commands `ca schedule apply [--env E]` (idempotent upsert via Temporal Schedule API — create or update to match config), `ca schedule ls` (config vs server drift, same spirit as `ca status`), `ca schedule rm <name>`. **[P2 amendment]** Also produces a shared start-args builder extracted from the existing deployed-run seam — `ca/temporal_run.py:44-65` currently builds the full `FlowInput` (flow_json, manifest_json, task_queue, bundle, pinned_pures → policy/principal/root, `harness.py:2354-2394`); that construction is factored into `build_flow_start_args(record: LedgerRecord, env: EnvConfig, input: Any) -> <workflow args>` used by BOTH `ca run` and `ca schedule apply`, so a scheduled run replays the deployed artifact with its pure-hash pins byte-identically to a manual `ca run`.
- Consumes: `EnvConfig.temporal_address/namespace/task_queue`; the deployed artifact ledger (schedules reference *deployed* flows — `apply` refuses a flow name absent from `.ca/deploys/<env>.json`, teaching error pointing at `ca deploy`).

Behavior:
- `apply` builds `temporalio.client.Schedule(action=ScheduleActionStartWorkflow(FlowWorkflow.run, args=build_flow_start_args(record, env, input), task_queue=env.task_queue), spec=ScheduleSpec(cron_expressions=[cron]))` with `schedule_id = f"ca:{env}:{name}"` — **never a hand-rolled args list**: bypassing the builder risks schedules that don't replay the deployed artifact or its pinned pures. Overlap policy SKIP (one running instance per schedule — matches mem-mcp's APScheduler + self-dedup posture); paused honored.
- Everything Temporal-touching lives behind the same lazy-import/`HAVE_TEMPORAL` guards the rest of `ca` uses; `ls`/parse-layer tests run without a server, `apply` integration test guarded.
- mem-mcp port note in the module docstring: the 24 APScheduler jobs become `[schedule.*]` tables; SQL-trigger enqueues (summary) stay app-side ingress, out of scope.

Tests: toml parse matrix (defaults, bad cron string → teaching error at parse via `croniter`-free regex sanity check: five/six fields), undeployed-flow refusal, schedule_id shape, apply/ls/rm against a fake client capturing calls; **builder equivalence** — the args a schedule's action carries are byte-identical (canonical JSON) to what `ca run` would start for the same ledger record + input; `ca run` refactored onto the shared builder with its existing tests still green; `@skipif` integration: apply → server schedule exists → rm → gone.

- [ ] TDD → gates → commit `feat(phase4): ca schedule — Temporal Schedules from ca.toml, drift-aware`

### Task 13: Queue lanes

> **[P1 amendment — direction change]** The original "lane is a whole-pipeline property, mixed-lane pipelines out of scope" stance is dropped. The public API already accepts per-subflow queues — `child.as_sub(queue="c3-q")` (`typed.py:70-75`) stores `SplitCapability.queue` (`typed.py:116-122`) and is tested (`tests/invariants/test_split.py:27-32`) — but the serialized subflow contract has no queue field (`ir.py:283-314`) and child workflow starts omit `task_queue` (`execution/harness.py:738`, `:851`, `:2420`), so the hint is silently inert today (a G-8 violation). And mem-mcp is role-laned well beyond two lanes: foreground / maintenance / summary / slack / brief-refresh / record-quality / record-execute (`docker-compose.unified-production.yml`). This task implements serialized per-subflow lane resolution.

**Files:**
- Modify: `composable_agents/ir.py` (subflow contract gains `queue`, omit-when-unset), `composable_agents/agent.py` + `composable_agents/deploy.py` (the agent split-children path: `SplitCapability.queue` serialized into the deployed agent spec, per-flow/agent `queue` deploy metadata), `composable_agents/execution/harness.py` (child workflow starts thread `task_queue` when resolved; `FlowInput`/`AgentInput` carry + propagate `queueLanes`, preserved across both continue-as-new sites), `composable_agents/ca/config.py` (`EnvConfig.queues: dict[str, str]`), `composable_agents/ca/cli.py` (`ca run --queue`, `serve`/worker selection), `composable_agents/execution/worker.py` (no change needed if task_queue already parametrized — verify)
- Test: `tests/ca/test_queue_lanes.py`, extend `tests/invariants/test_split.py`

**Interfaces:**
- Produces: `[env.prod.queues] foreground = "prod-fg" maintenance = "prod-maint" ...` — an n-lane map per env (ca.toml). Three layers, all omit-when-unset so every existing golden/ledger hash is byte-identical:
  1. **IR / spec — the FULL carrier path, not just the flow subflow contract**: `as_sub(queue=...)` lives on `SplitCapability` (`typed.py:116-122`), which is consumed by `Agent(tools=[child.as_sub(...)])` into `_split_children` (`agent.py:463-511`) — so `queue` must be serialized wherever split children land in the agent's deployed spec/contract, AND on the flow-level subflow contract in `ir.py` (both omit-when-unset; both stay env-independent, carrying the as-authored lane name or raw string). Tracing `SplitCapability.queue` from `as_sub` to the durable child start is an explicit implementation step: whichever serialized shapes it crosses (agent spec, subflow contract, tool-split descriptor) each gain the optional field.
  2. **Start input**: `FlowInput` AND `AgentInput` gain `queueLanes: Optional[dict[str, str]]` (omit-when-empty), populated from `EnvConfig.queues` by the shared start-args builder from Task 12 — so `ca run` and `ca schedule` deliver the same lane map, and lane resolution is deterministic (an input, not a config lookup inside the workflow). Propagation is transitive: every child-start site copies `queueLanes` into the child's `FlowInput`/`AgentInput`, and both continue-as-new sites (`harness.py:1188`, `:1626`) preserve it — otherwise nested subflows and long-lived agents/sessions silently lose lane resolution after the first hop.
  3. **Resolution at child start** (`harness.py` child `execute_child_workflow` sites — `:738`, `:851`, `:2420`): subflow queue present and in `queueLanes` → mapped concrete queue; present but not a known lane → used as the raw queue string; absent → inherit parent task queue (today's behavior, bit-for-bit).
- Whole-pipeline lanes: flows/agents opt into a lane via `deploy(..., queue="foreground")` recorded in the ledger (omit-when-unset → default `env.task_queue`); `ca run --env prod <flow>` starts the workflow on the flow's resolved lane; worker entrypoint gains `--queue <lane-name|raw>` (resolves lane through config, falls back to raw string).

Behavior:
- Replay safety: the new `queue`/`queueLanes` fields are additive and omit-when-unset — histories recorded before this task replay unchanged (the Task 11 corpus proves it). Child starts that resolve a queue produce a different first-run command, which is fine (new capability, not a mutation of existing behavior).
- Local/in-memory execution has no queues; lane hints are inert there by execution model (documented — same as activities running inline), not a silent fallback: `ca lint` surfaces subflow queues that name a lane missing from the target env's map (teaching error listing configured lanes).
- mem-mcp mapping note (module docstring + helm): the real role lanes above map to one worker Deployment + KEDA ScaledObject per lane (values example added to `infra/helm/ca-worker/values.yaml` as comments); interactive paths (RECORD plan/execute, checkin/recall) vs background (sweeps, rollups, clustering, dream) is the two-lane starter, not the ceiling.

Tests: config parse + default lane fallback; deploy metadata omit-when-unset (golden equality) and present-when-set; IR subflow contract round-trips `queue` and omits-when-unset (golden equality for queue-less flows); `ca run` resolves lane → start call captures expected task_queue (fake client); child-start resolution matrix (lane-mapped / raw-string / absent-inherits) via fake child-start capture; `as_sub(queue=...)` end-to-end: the invariants test extends to assert the queue survives the full carrier path from `SplitCapability` into the serialized agent spec/IR; `queueLanes` propagation matrix — copied into child `FlowInput`/`AgentInput` at every child-start site and preserved across continue-as-new (a nested-subflow fixture proves the second hop still resolves); worker `--queue` lane-name and raw-string resolution; unknown lane name → teaching error listing configured lanes.

- [ ] TDD → gates → commit `feat(phase4): queue lanes — per-env lane maps, serialized per-subflow queues, deploy-time lane selection`

---

## Acceptance

**Phase 3:** a mem-mcp-shaped tool-loop fixture (ported from `record/execute.ctx` semantics: 3 mock tools, `require_tool_call`, `max_rounds=12`, round notes) runs `drive_agent_loop(native_tools=True)` locally with a scripted provider: parallel calls execute effect-fenced, a raising tool becomes an observation the controller recovers from, transcript replays in provider grammar, and `ca eval` scores the run against a fixture eval suite with threshold + baseline gates. Full gates green; temporal e2e (`test_e2e_temporal.py`) green with `nativeTools` threaded.

**Phase 4:** anthropic calls with `prompt_cache="1h"` emit provider-safe cache markers (live-spike verified: creation then read tokens > 0) and every call records `prompt_cache_requested/applied/reason` + cache usage on `LlmCallMeta` — including inert/fallback cases (never silently dropped); a secret-shaped tool input never reaches the trajectory store raw because redaction runs at the capture seam before every blob write, and a mem-mcp-shaped value-level fixture redactor proves the injectable seam handles real memory/checkin/brief payloads; the replay corpus gates harness changes in CI across all six registered workflows; `ca schedule apply` starts deployed artifacts via the same start-args builder as `ca run` (builder-equivalence tested) and multi-lane workers with a per-subflow `as_sub(queue=...)` route demonstrated against the dev Temporal (guarded integration tests).

**Migration gate (recorded here so it is not lost — not satisfiable in this repo):** before mem-mcp enables trajectory capture in production, the mem-mcp repo must ship its own value-level redactor (hash-pointer style, covering memory text / checkin / brief content) injected through the Task 10 seam; the framework fixture redactor proves the seam, it does not discharge the PII precondition itself.

## Explicit non-goals

- Token streaming to end users, multimodal content, MCP client, CAS/wasm distribution work (unchanged roadmap items; mem-mcp needs none of them).
- Rate limiting / backoff jitter, budget-semantics unification across backends, native-downgrade latch refinement (real findings from the 2026-07-01 review, but not tool-loop gaps nor migration pre-conditions — tracked in TODOS.md).
- Migrating mem-mcp itself (per-agent ports happen in the mem-mcp repo against this feature set).
- Per-tenant credential resolution, Temporal server multi-env Terraform productionization (infra track, not framework). (Mixed-lane pipelines were a non-goal in the original draft; the 2026-07-02 review's P1 finding on the inert `as_sub(queue=...)` contract moved per-subflow lanes into Task 13.)
