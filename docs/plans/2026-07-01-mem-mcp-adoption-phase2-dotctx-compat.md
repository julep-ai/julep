# mem-mcp Adoption Phase 2: dotctx Compat Implementation Plan

> **For agentic workers:** execute task-by-task, TDD, commit after each task with prefix `feat(phase2):` / `fix(phase2):`.

**Goal:** Make composable-agents load all of mem-mcp's real `.ctx` prompts faithfully: `<<< role:... >>>` role-marker templates, single-file `.ctx` (YAML frontmatter + Jinja body), the `require_tool_call:` and `response_format:` settings keys (recorded declaratively; loop enforcement stays Phase 3/4), Yglu numeric-string coercion, and the `eval.py`/`eval.yaml` data surface (`sample()`/`score()` contract) — without executing eval code during prompt loading.

**Reference repo:** mem-mcp at `/home/diwank/github.com/julep-ai/mem-mcp`. Key sources:
- Loader semantics: `packages/python/dotctx/src/dotctx/loader.py` (`FRONTMATTER_PATTERN`, `ROLE_MARKER_PATTERN = <<<\s*role:(\w+)\s*>>>`, `_parse_role_markers`, `_load_single_file`, `_load_directory`).
- Eval surface: `packages/python/dotctx/src/dotctx/eval_types.py` (Sample, Expected, ExpectedToolCall, MockToolConfig, Turn, StopFn, stop_after_turns, stop_when_terminal_tool, stop_when_non_tool, any_stop, all_stop), `eval_loader.py` (EvalModule: required `sample(limit)` + `score(input, output, expected)` functions), `llm_utils.py` (`extract_llm_content`, `parse_llm_json`, `strip_markdown_codeblock`), `eval_config.py` (eval.yaml shape: models/datasets/threshold/concurrency/scoring/agent/profiles).
- Real prompts: `apps/memory-api/prompts/**/*.ctx` (33 dirs). Settings-key census across ALL of them: `model, temperature, output_retries, reasoning_effort, max_rounds, require_tool_call (5), response_format (4, always {type: json_object}), max_tokens`. Roles used: only `system` (26) and `user` (25). No `messages/` dirs; 6 `tools.pyi`.

**CA files touched:** `composable_agents/dotctx.py`, `composable_agents/dotctx_rich.py`, new `composable_agents/dotctx_evals.py`, `composable_agents/execution/llm.py`, `composable_agents/execution/llm_result.py` (only if a new meta key is needed — prefer riding the existing `response_format_fallback`), `composable_agents/deploy.py:_reasoner_identity` (line ~159).

## Global constraints

- Gates: `python -m pytest` (never bare pytest), `uv run mypy --strict composable_agents` (package only), `ruff check composable_agents tests`.
- No temporal dependence in new tests (the temporal=off CI job must stay green).
- Existing deploy goldens must be byte-for-byte unchanged: new identity fields enter `_reasoner_identity` omit-when-unset, following the existing convention.
- G-8: no silent fallbacks — unsupported values are loud teaching errors; provider fallbacks are recorded on `LlmCallMeta`.
- jinja2 stays behind the `[dotctx]` extra; yglu behind `[yglu]`; `dotctx_evals.py` must import cleanly without either (lazy imports where needed).
- Loading a `.ctx` must NEVER execute `eval.py` — eval loading is a separate, explicit entry point.

---

### Task 1: Role-marker splitting in the rich loader

**Files:** `composable_agents/dotctx_rich.py`; tests in `tests/test_dotctx_rich.py` (extend).

Behavior:
- `prompt.j2` whose source matches `<<<\s*role:(\w+)\s*>>>` is split into per-role template sources. Marker line spacing is flexible (`<<<role:system>>>` also matches, mirroring mem-mcp's regex).
- v1 accepts exactly the shapes the `messages/` bundle accepts: one `system` section, optionally followed by one `user` section. Duplicate roles, other roles (`assistant`, ...), or user-before-system → `ValueError` naming the file and the offending role (teaching error).
- Content before the first marker must be blank or Jinja comments/whitespace only; it is prepended to the system section source (preserves `{# AI-ANCHOR #}` headers, renders to nothing). Non-comment leading text → `ValueError`.
- No markers → existing behavior (whole file is the system template).
- Split sections register as separate renderers (`system`/`user` roles), exactly like a `messages/` bundle does today — same downstream `system_render`/`user_render` wiring, no Reasoner changes.

Tests: real-shape fixture string (jinja comment header + system + user, copied in spirit from `episode_summary.ctx/prompt.j2`); tight-spacing markers; unknown role errors; duplicate system errors; user-first errors; no-marker file unchanged behavior; renderers render with StrictUndefined context.

- [ ] Write failing tests → implement → `python -m pytest tests/test_dotctx_rich.py -v` → mypy + ruff → commit `feat(phase2): role-marker template splitting in rich dotctx`.

### Task 2: Single-file `.ctx` support

**Files:** `composable_agents/dotctx.py`, `composable_agents/dotctx_rich.py`; new tests `tests/test_dotctx_single_file.py`.

Behavior:
- `load_dotctx(path)` where `path` is a **file** ending `.ctx`: parse with mem-mcp's frontmatter regex `^---\n(.*?)\n---\n(.*)$` (DOTALL). Frontmatter YAML goes through the same Yglu-aware settings path as `settings.yaml` (refactor `dotctx_rich._read_settings`'s text-parsing core into a shared helper so both call it; keep `has_yglu_tags` gating). Body = template, split by Task 1's role-marker logic.
- Single-file `.ctx` always routes through `dotctx_rich` (the body is a template ⇒ jinja2 required; same hard ImportError without the extra).
- No frontmatter match → empty settings `{}` (mirrors mem-mcp; CA's existing defaults apply). Reasoner name defaults to the filename stem without `.ctx`.
- `is_rich_dotctx` and directory handling unchanged; a directory named `foo.ctx` keeps working.
- Rich-loader unknown-settings-key validation applies to frontmatter identically.

Tests: frontmatter + role-marker body loads (model/temperature/name asserted); yglu `!?`-tagged frontmatter with explicit `env=` mapping; no-frontmatter file → template-only + defaults; frontmatter-only (no markers) → system template; non-`.ctx` file → clear error; missing file → clear error.

- [ ] TDD as above → commit `feat(phase2): single-file .ctx (frontmatter + template body)`.

### Task 3: `require_tool_call` / `response_format` keys + Yglu numeric coercion

**Files:** `composable_agents/dotctx.py` (`Reasoner`, `reasoner_from_settings`, `_model_and_effort` area), `composable_agents/dotctx_rich.py` (`_ALLOWED_SETTINGS`), `composable_agents/deploy.py` (`_reasoner_identity`), `composable_agents/execution/llm.py`; tests: `tests/test_dotctx_reply.py` / `tests/test_dotctx_rich.py` extensions, `tests/execution/` llm tests near the existing response_format-fallback tests, deploy golden test run.

Behavior:
- New frozen `Reasoner` fields (constructor keyword-only, defaults preserved): `require_tool_call: bool = False`, `response_format: Optional[str] = None`.
- Settings parsing (both loaders, snake and camel variants): `require_tool_call:` → bool; `response_format:` must be a mapping `{type: json_object}` → stored as `"json_object"`; any other shape/type → teaching `ValueError` listing the supported form. Declaring both `response_format` and a reply schema is allowed; the schema wins at call time (document in docstring).
- `require_tool_call` is declarative in Phase 2: carried on the Reasoner and hashed into identity; agent-loop enforcement is explicitly Phase 3/4 (docstring note).
- Yglu/env values arrive as strings: coerce numeric strings for `max_rounds`, `max_tokens`, `output_retries` (int) and `temperature` (float) in both loaders; non-numeric strings → teaching `ValueError`. (Real case: `record/execute.ctx` has `max_rounds: !? $env.get("RECORD_EXECUTE_MAX_ROUNDS", 12)`.)
- `deploy.py:_reasoner_identity`: `if reasoner.require_tool_call: ident["requireToolCall"] = True`; `if reasoner.response_format is not None: ident["responseFormat"] = reasoner.response_format`. Omit-when-unset ⇒ existing goldens byte-identical (assert by running the deploy golden tests unchanged).
- `execution/llm.py`: when `reply_schema` is None and `reasoner.response_format == "json_object"`, send `response_format={"type": "json_object"}` through the same path as schema-derived response_format: honor `_PROMPT_FALLBACK_PROVIDERS`, the `native_ok` latch, and the recorded-fallback contract. Fallback behavior for json_object is to reissue WITHOUT the kwarg and record `response_format_fallback` (no prompt injection — mem-mcp prompts self-instruct JSON). CONFIG-class errors still re-raise (Phase 1 rule). When both schema and json_object are present, schema path wins (no double kwarg).

Tests: loader parsing (true/false/absent; json_object; bad shapes error); coercion matrix incl. yglu-loaded settings; identity omit-when-unset (golden equality + new-field presence when set); llm fake-provider test: json_object kwarg sent; unsupported-provider fallback recorded once and latched; schema-wins precedence.

- [ ] TDD → full gates → commit `feat(phase2): require_tool_call + response_format(json_object) settings, identity, provider wiring`.

### Task 4: eval compat — `composable_agents/dotctx_evals.py`

**Files:** new `composable_agents/dotctx_evals.py`; new `tests/test_dotctx_evals.py`; docstring pointer update in `dotctx_rich.py` (it currently says eval files "are ignored here").

Behavior — a faithful port of mem-mcp's eval *data* surface (no runner):
- Types/functions ported 1:1 from `eval_types.py`: `Input`/`Output`/`Score` aliases, `Turn`, `StopFn`, `stop_after_turns`, `stop_when_terminal_tool`, `stop_when_non_tool`, `any_stop`, `all_stop`, `ExpectedToolCall`, `Expected`, `Sample`, `MockToolConfig`. Ported from `llm_utils.py`: `strip_markdown_codeblock`, `extract_llm_content`, `parse_llm_json` (read the mem-mcp sources and mirror behavior, including edge cases).
- `EvalModule` dataclass + `load_eval_module(path) -> EvalModule`: exec the `eval.py` via importlib spec (unique module name), requiring callable `sample` and `score` with mem-mcp's exact error messages shape (teaching errors). Before exec, install compat aliases in `sys.modules` for `dotctx`, `dotctx.eval_types`, `dotctx.llm_utils` pointing at this module's namespaces — ONLY for names not already importable (never clobber a real installed `dotctx`), and restore `sys.modules` in a `finally`. Document: CLI/test-time only, not thread-safe (same caveat as the Phase 1 yglu env swap).
- `load_eval_config(path) -> EvalConfig`: parse `eval.yaml`/`eval.yml` (Yglu-aware via `dotctx_yglu`, explicit `env=` param) into a small typed dataclass: `models` (list of {id, tags}), `datasets` (list of {file, format, tags}), `threshold: float`, `concurrency: int`, `scoring: dict`, `agent: dict`, `profiles: dict[str, EvalConfig-shaped overrides]`. Unknown top-level keys → teaching error. Data only — no evaluation execution.
- `load_ctx_evals(ctx_dir, *, env=None) -> CtxEvals` (eval_module + eval_config, either Optional): the ONE explicit entry point. `load_rich_dotctx` must NOT call it.

Tests: a fixture eval.py using `from dotctx.eval_types import Sample` + `from dotctx import extract_llm_content` loads via the shim; missing `sample`/`score` → teaching errors; `sys.modules` is clean after load (and untouched keys preserved); eval.yaml with yglu `!?` + explicit env parses; profiles resolve as raw data; `extract_llm_content`/`parse_llm_json`/`strip_markdown_codeblock` behavior matrix mirrored from mem-mcp (fenced JSON, dict responses, nested output).

- [ ] TDD → gates → commit `feat(phase2): dotctx eval compat surface (sample/score contract, eval.yaml config)`.

### Task 5: Real-prompt fixtures + sibling-repo sweep + docs

**Files:** `tests/fixtures/memmcp/` (new), `tests/test_memmcp_compat.py` (new), doc touch: `docs/` dotctx page if present (else module docstrings suffice).

- Vendor real mem-mcp prompt content as fixtures (trim long prose bodies is fine; keep structure exact): `episode_summary.ctx/` (jinja-comment header + role markers + Input-only schema.pyi + yglu model + eval.py+), a `require_tool_call` settings dir modeled on `record/execute.ctx` (yglu `max_rounds`), `cluster_label.ctx`-style dir (`response_format: {type: json_object}`), one single-file `.ctx` in mem-mcp's frontmatter format, and an `eval.yaml` modeled on `briefs/draft.ctx`.
- `test_memmcp_compat.py`: load every fixture with explicit `env={}`; assert canonical model, effort, require_tool_call/response_format fields, renderer split, eval module/config loading (eval via `load_ctx_evals`, proving prompt-load didn't exec it).
- Sweep test guarded by `pytest.mark.skipif(not os.path.isdir("/home/diwank/github.com/julep-ai/mem-mcp"), ...)`: glob `apps/memory-api/prompts/**/*.ctx` in the sibling repo and `load_dotctx(..., env={})` every one (fresh Registry per load or unique names to avoid collisions — check `register_reasoner` semantics for re-registration and handle deliberately). All 33 must load. Do NOT load eval modules in the sweep (arbitrary code; the fixture test covers eval loading).
- [ ] TDD → full gates (`python -m pytest`, mypy --strict, ruff) → commit `feat(phase2): mem-mcp prompt fixtures + sibling-repo compat sweep`.

## Acceptance

All 33 mem-mcp `.ctx` prompts load through `load_dotctx` with `env={}`; role-marker prompts produce system+user renderers; `require_tool_call`/`response_format` are recorded on the Reasoner and in deploy identity (goldens unchanged); eval sample/score modules and eval.yaml configs load through the explicit compat entry; full gates green.

## Explicit non-goals (Phase 3/4)

- Enforcing `require_tool_call` in the agent loop; native tool-calling.
- Running evals (runner, scoring loops, mock-tool execution, costs) — Phase 2 only loads them.
- MCP client, resilience-policy port, sub_deployments, CAS/wasm distribution.
