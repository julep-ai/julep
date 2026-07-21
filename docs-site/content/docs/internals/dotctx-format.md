---
title: "dotctx Format"
description: "The rich .ctx reasoner-definition format."
---

> Status: design draft 2026-06-10, decided with mem-mcp (option B2 of the
> adoption sketch: this adapter becomes the canonical dotctx; rejected: a
> bridge package in mem-mcp keeping two formats alive, and a shared third
> package extracted up front). Builds directly on
> `docs/plans/2026-06-07-prompt-renderers.md` (registered renderers,
> `Reasoner.system_render`, the projected `Context`) and
> `docs/design/prompt-fragments.md`. The consumer driving this is
> mem-mcp's 25 production `.ctx` prompt packages
> (`apps/memory-api/prompts/**/*.ctx`).

## Thesis

This repo's dotctx adapter (`julep/dotctx.py`) reads a minimal
layout — `settings.yaml`, inline/`system_file` prompt, optional
`schema_file` — into a `Reasoner`, and its `max_rounds` lowering to IR shape is
the part worth keeping exactly as is. mem-mcp's production dotctx is the same
idea grown rich: Jinja2 templates, multi-message bundles
(`messages/00_system.yml`, `01_user.yml`), input/output schemas and tool
definitions derived from `.pyi` stubs, and per-package evals. Today the two
formats share a name and nothing else.

Decision: **this adapter is canonical and grows to read the rich layout
natively**, behind an optional extra, so mem-mcp's packages migrate onto it
rather than being bridged forever. The pure core stays dependency-free; what
enters the deploy artifact stays **strings and JSON only** (renderer *names*,
not templates; JSON Schema, not pydantic models), so freeze hashes and the
golden corpus do not move.

## The rich layout (target)

```
<name>.ctx/
├── settings.yaml        # name, model, temperature, max_rounds, agent, sub, context, tools
├── schema.pyi           # input/output models -> reply_schema (JSON Schema)
├── tools.pyi            # tool stubs -> granted tool keys + expected schemas
├── prompt.j2            # single-template form (optional <<< role:... >>> markers), OR
└── messages/            # multi-message form
    ├── 00_system.yml    # role: system, Jinja2 body
    └── 01_user.yml      # role: user, Jinja2 body
eval.py / eval.yaml      # never read by prompt loading (see mem-mcp compat)
```

`load_dotctx(path)` keeps working for the existing minimal layout; the rich
fields are detected by file presence. One loader, one format, additive.

### mem-mcp compat (Phase 2, 2026-07-01)

The loader reads mem-mcp's production prompts unchanged:

- **Role markers.** A `prompt.j2` split by `<<< role:system >>>` /
  `<<< role:user >>>` markers registers one renderer per role — the exact
  shapes a `messages/` bundle accepts. Content before the first marker must
  be whitespace, Jinja comments, or bare `#` header lines (`# AI-ANCHOR`
  convention; dropped like mem-mcp drops all pre-marker content).
- **Single-file `.ctx`.** A *file* path is mem-mcp's compact form: YAML
  frontmatter between `---` lines (same settings path, same unknown-key
  validation) plus a Jinja body with optional role markers.
- **Settings keys.** `require_tool_call:` (declarative on the `Reasoner`;
  loop enforcement lands in Phase 3/4) and
  `response_format: {type: json_object}` (stored as `"json_object"`; a reply
  schema wins at call time). Both enter deploy identity omit-when-unset.
- **Yglu.** Settings and frontmatter may carry `!? $env.get(...)` expressions
  (`julep[yglu]`), evaluated against an explicit `env=` binding —
  never the ambient process environment. Numeric strings arriving from env
  coerce for `max_rounds` / `max_tokens` / `output_retries` / `temperature`.
- **Jinja filters.** mem-mcp's pure filters (`to_json`, `as_xml`,
  `as_codeblock`, `numbered_list`, `bulleted_list`, `dedent`, `from_json`)
  are ported 1:1 onto the render environment; the file/token filters
  (`import_yaml`, `import_text`, `count_tokens`, `truncate_tokens`) compile
  but raise a teaching error at render (they need mem-mcp's
  base_dir/tokenizer wiring).
- **Evals.** `eval.py` (required `sample(limit)` + `score(input, output,
  expected)`) and `eval.yaml` load only through the explicit
  `julep.dotctx_evals.load_ctx_evals` entry point — loading a
  prompt never executes eval code. Running evals stays a consumer concern.

## Design

### Packaging

New optional extra: `julep[dotctx]` → `jinja2` (PyYAML is already
required for any disk loading). The rich loader lives in
`julep/dotctx_rich.py`; importing it without the extra raises
immediately (no degraded parse — G-8 discipline: a package that *has* a
`prompt.j2` and a loader that can't render it is a hard error, not a
plain-string fallback).

### Templates become registered renderers

A `prompt.j2` or `messages/*.yml` body is **never** stored on the `Reasoner` and
never enters the artifact. Loading compiles each template and registers **one
renderer per template**, named by role:
`dotctx/<package-name>/system@v<content-hash-prefix>` for the system body and
`dotctx/<package-name>/user@v<content-hash-prefix>` for a bundle's user body —
each hashed like any registered pure so §6.4 drift detection covers prompt
edits to either. The `Reasoner` gets `system_render` and (for bundles)
`user_render` set to the matching names; `Reasoner.system` stays `""`.

Renderer input is the projected `Context` from the prompt-renderers plan. The
Jinja2 environment is strict (`StrictUndefined`), with no filesystem loader at
render time — templates are compiled at load, rendered from `Context` only.
A template referencing a variable the `Context` doesn't carry fails at first
render with the package name and variable in the error.

### Message bundles: add `user_render`

The current invoke path is system + value-as-user
(`execution/llm.py:137-169`). Bundles need the user turn templated too:

- `Reasoner` gains `user_render: Optional[str]` exactly symmetric to
  `system_render` (string name, conditional-key inclusion in the codec so
  existing hashes are stable).
- `rendered_reasoner_for(reasoner, value)` extends to produce the rendered user
  string; `complete_reasoner` uses it as the user turn when present, else the
  current value-as-JSON behavior.
- Bundles with roles beyond one system + one user (e.g. few-shot assistant
  turns) are **out of v1**; the loader rejects them loudly with the file
  name. mem-mcp's current bundles are system+user; revisit if a real package
  needs more.

### `schema.pyi` → `reply_schema`

The loader compiles the output model in `schema.pyi` to plain JSON Schema at
load time and sets `Reasoner.reply_schema`. mem-mcp's dotctx already has this
compiler (`packages/python/dotctx/src/dotctx/tools_parser.py` and the schema
parser beside it); the port brings the *compiler* in under the extra, not
pydantic — the artifact carries JSON Schema, the runtime validates JSON, and
`reply_schema` flows through `complete_reasoner`'s existing structured-output
path (native `response_format` where the provider has it, prompt-injected
schema where it doesn't).

### `tools.pyi` → grants + freeze-time verification

`tools.pyi` stubs name the tools the reasoner may call, with their schemas. The
loader does two things:

1. Sets `Reasoner.tools` to the toolref keys (`server/tool` for MCP tools), and
   emits a **manifest fragment** (a `ToolGrant` list) the caller merges into
   the deployment's `CapabilityManifest` — packages declare what they need;
   the deployment still decides what is granted.
2. Records the expected input schema per tool. At freeze, when the MCP
   snapshot resolves those tools, the framework compares expected vs. served
   schema by canonical hash and raises a blocking diagnostic on mismatch
   (`TOOL_SCHEMA_DRIFT`, with the `.ctx` path and the server name). A prompt
   written against one tool contract silently running against another is
   exactly the class of bug freeze exists to stop.

The stubs do **not** create tools. The tools are served by real MCP servers
(for mem-mcp: its internal task-family servers); `tools.pyi` is the
prompt-side contract assertion.

### Settings normalization

Accepted keys grow to cover mem-mcp's settings: `max_tokens` (stored on
`Reasoner`, forwarded by the LLM caller), `model` with the `@low/@medium/@high`
reasoning-effort suffix **passed through untouched** — effort is an
`LlmCaller` convention (mem-mcp's caller maps it to provider payloads), not a
framework concern. Unknown keys are a load-time error listing the offending
keys, not a warning.

## Migration (mem-mcp's side, summarized here for shape)

Of the 25 packages: the single-`think` majority (summaries, labels, rollups,
rewrites) load as bounded reasoners with no edits beyond settings-key renames;
the tool-using packages (`record/execute`, brief pipeline) additionally rely
on `tools.pyi` grants + freeze verification; provider-transform logic in
mem-mcp's dotctx package is **deleted**, superseded by the `LlmCaller`.
Details live in mem-mcp `specs/042-julep-temporal/`.

## Non-goals

- **Running evals.** Prompt loading ignores `eval.py`/`eval.yaml`; Phase 2
  loads them as data via `dotctx_evals.load_ctx_evals` (above), but the
  runner, scoring loops, and mock-tool execution stay consumer-side.
- **Few-shot / arbitrary-role bundles** (above).
- **A pydantic runtime dependency.** JSON Schema in, JSON out.

## Touch set

| File | Change |
|---|---|
| `julep/dotctx.py` | `user_render`, `max_tokens` on `Reasoner`; rich-layout detection delegating to `dotctx_rich` |
| `julep/dotctx_rich.py` | create: Jinja2 compile + renderer registration, message-bundle parse, `.pyi` schema/tool compilers, manifest-fragment emission |
| `julep/prompt.py` | `rendered_reasoner_for` covers `user_render` |
| `julep/execution/llm.py` | user turn from rendered user string; forward `max_tokens` |
| `julep/freeze.py` | `TOOL_SCHEMA_DRIFT` check against recorded expected schemas |
| `julep/ir.py` / codec | conditional-key inclusion for new Reasoner fields (hash-stable) |
| `pyproject.toml` | `dotctx` extra |
| `docs/SPEC.md` | rich layout, renderer naming/hashing, drift diagnostic |
| tests | minimal-layout regression; rich load of a fixture `.ctx`; renderer drift; bundle rejection cases; schema-drift diagnostic; golden corpus unmoved |

<!-- ported-by julep-docs-site: internals/dotctx-format -->
