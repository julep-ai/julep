# Composable-agents developer CLI (`ca`) — design

**Date:** 2026-06-22
**Status:** Mental model + command surface converged in brainstorming; ready for v1 implementation plan
**Scope:** A developer-facing CLI (`ca`) that operates on a **module of `@flow` agents authored in Python source** — lint, test, run, debug, deploy, instrument, and tail logs/traces across the whole module. It is *porcelain* over the existing `composable-agents` JSON-artifact *plumbing*. **Not** a new runtime, a new backend, or a bundled web UI.

---

## 1. Goal

Today the `composable_agents` framework has rich Python APIs (in-memory `dry_run`, Temporal durable workflows + Helm/KEDA, CMA, DBOS, projection→OTel→Langfuse) and a low-level CLI (`composable-agents validate|freeze|inspect|run-local|graph|worker`) that operates on **frozen JSON artifacts**. The explorer's one-line verdict on the current state: *"No module-level group/deploy/run CLI exists."*

The goal is to close that gap with a single cohesive CLI whose mental model is **"dbt for agents, terminal-native, local-first"**:

1. Point `ca` at a directory; it **auto-discovers** every `@flow` agent and treats each as a node in a cross-agent dependency graph (edges = `app`/`sub` calls).
2. **One selection grammar** addresses any slice of that graph, used *identically* by every verb (lint / test / run / deploy / trace / viz).
3. A **local hot-reload dev loop** (`ca dev`) is the inner cycle; **Temporal/EKS + Langfuse** are the faithful outer cycle.
4. Observability is **terminal-native first** (trace trees, live tail, step inspection) with **Langfuse deep links** for the rich web view — reusing the OTLP export landing on the `langfuse-integration` branch.

## 2. Decisions (locked during brainstorming)

| Decision | Choice | Rationale |
|---|---|---|
| Primary outcome of this phase | **Converge mental model + command grammar**, then carve v1 | User chose model-first; the command *shape* is the deliverable, with a v1 slice marked. |
| Addressable unit | **Agents are the nodes** | Module = set of `@flow` agents; selectable unit = an agent. Cross-agent `app`/`sub` calls form the dependency graph (dbt "model"-style). Intra-agent steps are a drill-down detail, not first-class selectable. Simplest mental model. |
| Discovery | **Convention + optional config** | Auto-discover all `@flow`s by default (zero-config, drift-free). An optional committed config layers env / deploy targets / gate thresholds and can pin/exclude agents. Progressive disclosure. |
| Execution locus | **Local-first dev server** | `ca dev` boots a local in-memory loop with hot-reload + live terminal trace; deploy is a *separate* push to Temporal/EKS. Magical inner loop; prod stays faithful via the outer loop. |
| Debug/trace surface | **Terminal-native first** | Trace tree, step inspection, and live tail render in the terminal (stern/Stripe-style); Langfuse deep links for the rich web view. No bundled web UI to design or maintain. Fully scriptable. |
| Binary | **New `ca` porcelain wrapping existing `composable-agents` plumbing** | Short; matches the `ca.cid`/`ca.node` span prefix. The JSON-artifact commands stay as the lower layer; `ca worker` remains the deploy-time entrypoint. |
| `eval` vs `test` | **Split: `ca eval` for the rich grid/regression UX; `ca test` runs evals too** | Evals are a kind of test (so CI's `ca test` covers them), but the prompt×provider×case grid + regression diff deserves its own verb. |
| v1 selector scope | **`name` + `tag:` + `state:modified`**; graph operators (`+agent`, `@agent`, `agent+2`) deferred | The directional graph algebra is high-value but heavy; ship the 80% first. The grammar is designed so operators slot in later without breaking callers. |

### Rejected / deferred during brainstorming

- **"Everything is a node"** (tools/pures/reasoners individually selectable, dbt-where-seeds-and-sources-coexist). More expressive, but a heavier mental model than the agent-centric view buys for the target user. Intra-agent artifacts remain visible via `ca show <agent>`, just not top-level selectable.
- **Two-level explicit addressing** (`agent:step` as a separate grammar). Rejected for v1 in favor of agents-as-nodes with step drill-down inside `ca show`/`ca trace`.
- **Bespoke local web studio** (editable context window / time-travel / chat→promote-to-eval, à la Letta/LangGraph). High differentiation but a real frontend to own. Deferred; the terminal-native surface + Langfuse deep links cover the need first. Kept as a north-star (§9).
- **Backend-as-target (`--env` swaps in-mem vs Temporal for the *inner* loop)** and **cloud-first control plane**. Both rejected as the *center of gravity* in favor of local-first — but `--env` still selects the **deploy/observe** target in the outer loop (§6).

## 3. The mental model

```
  A MODULE = a directory of @flow agents
  ───────────────────────────────────────────────────────────────
        triage ──app──► escalate ──sub──► notify
          │                                  ▲
          └────────────── tag:support ───────┘
  ───────────────────────────────────────────────────────────────
  Each agent is a NODE. Edges are app/sub calls → the module graph.
  One selection grammar slices this graph for every verb.

  TWO LOOPS, ONE GRAMMAR
  ───────────────────────────────────────────────────────────────
  inner (local, magical)        outer (prod, faithful)
    ca dev   ── hot reload         ca deploy --env staging|prod
    ca run   ── in-mem dry_run     ca logs -f / ca trace <run-id>
    ca chat  ── REPL               ca status / ca doctor
    └─ live terminal trace         └─ Temporal/EKS + Langfuse deep links
```

**Porcelain over plumbing.** `ca` never re-implements core logic. It *discovers source*, builds the module graph, applies selectors, and calls the existing APIs/CLI underneath:

| Porcelain (`ca`) | Plumbing it drives |
|---|---|
| `ca run` / `ca dev` | `deployment.dry_run(...)`, `execution/interpreter.py` (in-memory `Env`) |
| `ca lint` | `ruff`, `mypy --strict`, `validate.py` diagnostics, `freeze.py`/`capabilities.py` checks |
| `ca test` / `ca eval` | `pytest`, `tests/golden` corpus, eval runner (new thin layer) |
| `ca deploy` | `deploy.py` (`deploy()`/`Deployment`), `freeze`, image build, Helm/KEDA `ca worker` |
| `ca logs` / `ca trace` | `projection.py` → `execution/otel.py` → `execution/langfuse.py`; Temporal history |
| `ca graph` / `ca show` / `ca ls` | `dag.py`, `ir.py`, registry/discovery |

## 4. Architecture

```
                         ┌─────────────────────────────────────────┐
  source dir ──discover──►  Module model (in-memory)                │
   (@flow scan)           │   agents[], cross-agent app/sub edges,  │
   + optional config      │   tags, deploy status, gate config      │
                          └───────────────┬─────────────────────────┘
                                          │  SELECTOR resolves to a node set
                          ┌───────────────┴─────────────────────────┐
                          ▼                ▼                ▼        ▼
                       ca lint          ca run/dev       ca deploy  ca logs/trace
                          │                │                │        │
                     ruff/mypy/        dry_run /         deploy()/  projection→otel
                     validate          interpreter       freeze/     →langfuse +
                     (findings,        (terminal         worker      Temporal hist
                      severity,         trace tree)      (Helm/KEDA)  (terminal tree
                      exit codes)                                      + deep link)
```

**Discovery (the module model).** A `discover(path)` step imports the package, collects every `FlowDef` (the `@flow` decorator already captures source + AST), reads `app`/`sub` references to build edges, and merges the optional config (env, deploy targets, gate thresholds, pin/exclude). Output is a pure in-memory `Module` object — the single source of truth every verb consumes. This is the one genuinely new core-ish component; everything else is orchestration.

**Selector engine.** `select(module, expr) -> set[Agent]`. v1 methods: bare `name`, `tag:<t>`, `path:<glob>`, `state:modified` (diff vs git/last-freeze), `result:fail` (last run). Set ops: space = union, comma = intersection; `--exclude EXPR`. Graph operators (`+a`, `a+`, `@a`, `a+N`) are a post-v1 extension point on the same engine.

**No new runtime.** `ca` is stateless between invocations except for a small local cache (last run results for `result:`/`state:`, dev-server PID). All durability stays in Temporal/Postgres/Langfuse.

## 5. Command surface

```
# Inspect the module graph
ca ls [SELECTOR]            list agents + tags + deploy status            (dbt ls / dagster list)
ca graph [SELECTOR]         render the cross-agent app/sub DAG            (extends today's `graph`)
ca show <agent>             one agent: inputs, tools/pures/reasoners, caps, step DAG

# Inner loop — local-first
ca dev                      auto-discover + hot-reload + in-mem backend + live trace tail   ★centerpiece
ca run <agent> --input ...  execute once locally, stream terminal trace tree
ca chat <agent>             interactive REPL against an agent

# Gates
ca lint [SELECTOR]          ruff + mypy + validate/diagnostics + capability/freeze checks
ca test [SELECTOR]          pytest + golden corpus (+ evals) for the selected slice
ca eval [SELECTOR]          evals-as-tests: cost/latency/rubric asserts, regression diff

# Outer loop — deploy + observe
ca deploy [SELECTOR] --env  freeze + push to Temporal/EKS; immutable artifact + rollback
ca logs [SELECTOR] -f       tail durable runs; color-per-run; auto-attach new runs   (stern-style)
ca trace <run-id>           terminal trace tree + clickable Langfuse deep link  (`--follow` live)
ca status --env             what's deployed where + drift vs local       (supabase migration list)
ca doctor                   preflight: Temporal / Langfuse / env / extras check  (fly doctor)
```

Every command that takes `[SELECTOR]` accepts the §6 grammar. Commands degrade gracefully: with no Temporal extra installed, outer-loop commands print an actionable `ca doctor`-style hint rather than a stack trace.

## 6. Selection grammar

Used identically by `ls`, `graph`, `lint`, `test`, `eval`, `run`, `deploy`, `logs`.

| Form | Meaning | v1? |
|---|---|---|
| `triage` | agent by name | ✅ |
| `tag:support` | all agents carrying a tag | ✅ |
| `path:examples/*.py` | agents defined under a path glob | ✅ |
| `state:modified` | agents whose source changed vs git HEAD / last freeze | ✅ |
| `result:fail` | agents whose last local run failed | ✅ |
| `a b` (space) | union | ✅ |
| `a,b` (comma) | intersection | ✅ |
| `--exclude EXPR` | subtract a set | ✅ |
| `+triage` / `triage+` / `@triage` / `triage+2` | upstream callers / downstream callees / both / depth-bounded | ⏳ post-v1 |

**Environment is orthogonal to selection.** `--env local|staging|prod` (default `local`) selects the *target backend* for outer-loop verbs and is read from the optional config's env table. `state:modified` enables dbt-style Slim CI: `ca test state:modified` / `ca deploy state:modified --env staging`.

## 7. Gate semantics (lint / test / eval)

Convergent pattern stolen from Terraform / Spectral / dbt / promptfoo:

- **Findings carry severity** — `ERROR` / `WARN` / `INFO` — and a **named, suppressible rule ID** with remediation text (e.g. `capability-ungranted`, `pure-unregistered`, `shape-mismatch`, `freeze-drift`).
- **`--fail-severity {error,warn,info}`** (default `error`) decouples *what is reported* from *what fails the build*. Everything is always reported; only the threshold gates.
- **Tiered exit codes:** `0` clean · `1` findings at/above `--fail-severity` · `2` tool/usage error. (`ca status` may add a Terraform-style `3 = drift detected` for CI.)
- **`--json`** on every gate for machine consumption; human-readable is the default.
- **Evals** (`ca eval`): assertions inline in config — deterministic (`contains`, `regex`, `is-json`, **`cost`**, **`latency`**) and model-graded (`llm-rubric`); per-eval `threshold`; a regression diff vs a stored baseline (promptfoo/Braintrust-style). `ca test` invokes the same runner so CI gets evals for free.

## 8. Configuration (convention + optional)

Zero-config works: `ca` in any dir with `@flow`s. The optional committed config (name TBD: `ca.toml` / `[tool.ca]` in `pyproject.toml` — see open questions) adds only what convention can't infer:

```toml
[tool.ca]
src = ["agents/", "examples/"]        # discovery roots (default: cwd package)
exclude = ["examples/scratch_*.py"]

[tool.ca.tags]                         # optional explicit tags if not on @flow
triage = ["support"]

[tool.ca.env.staging]
temporal_address = "..."
temporal_namespace = "..."
task_queue = "ca-staging"
langfuse_host = "..."

[tool.ca.gates]
fail_severity = "error"
```

The config is reviewable, drift-detectable (`ca status`), and never required to *start*. Secrets are injected from the environment (Doppler-style), never written here.

## 9. v1 slice vs north-star

**v1 (buildable first):** `discover` + `Module` model + selector engine (name/tag/path/state/result, set ops, `--exclude`) + `ca ls`, `ca show`, `ca graph`, `ca run`, `ca lint`, `ca test`, `ca trace <run-id>` (terminal tree + Langfuse link), `ca doctor`. This is a complete inner-loop + gates + single-run observability story on top of existing plumbing. Note: the inner loop *exists* in v1 via `ca run` (one-shot local execution + terminal trace); `ca dev` (§3's centerpiece) is the *elevated* form of that same loop — hot-reload + persistent live tail — and lands in v1.5 once `ca run` proves the in-memory trace rendering.

**v1.5:** `ca dev` (hot-reload server + live tail — the inner loop's full realization), `ca logs -f` (stern-style multi-run tail), `ca eval`, `ca deploy`/`ca status`, `--env` targets.

**North-star (deferred, not discarded):** graph selection operators; `ca chat` REPL; Stripe-style `ca listen --forward-to` / `ca trigger <event>` for event debugging; the bespoke web studio (editable context window, time-travel re-run, chat→promote-to-eval).

## 10. Non-goals

- No new execution backend or durability layer — `ca` orchestrates existing ones.
- No bundled web UI in any milestone here — Langfuse is the web surface.
- No replacement of the `composable-agents` JSON-artifact commands — `ca` wraps them.
- Not a prompt-management or dataset product (that's Langfuse/other tooling).

## 11. Open questions (for the plan / review)

1. **Config location** — `ca.toml` vs `[tool.ca]` in `pyproject.toml` vs reuse an existing project file. Leaning `[tool.ca]` to avoid a new file (progressive disclosure ethos).
2. **CLI framework** — Typer vs Click vs argparse (existing `cli.py` is argparse). Typer buys help/UX cheaply; argparse keeps the zero-dep core. Likely Typer in a `dev`/CLI extra so core stays dependency-light.
3. **Discovery cost** — importing a package to scan `@flow`s runs module-level code. Need an import sandbox / guard so discovery is safe and fast (Dagster `dg check defs` precedent).
4. **`state:modified` baseline** — diff against git HEAD, the working tree, or the last frozen artifact hash? Probably git-tree by default with `--state <ref>` override.
5. **Trace tree source for local runs** — render directly from in-memory projection events (no Langfuse round-trip), and only deep-link Langfuse for deployed runs? Leaning yes.
