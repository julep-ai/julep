# `ca` — the developer CLI

`ca` is the developer-facing CLI for a **module of agents**. Where `composable-agents` (the plumbing CLI) operates on frozen JSON artifacts, `ca` operates on your **Python source**: point it at a directory and it discovers every `@flow` and `Agent(...)`, treats each as a node in a cross-agent dependency graph, and gives you one selection grammar to inspect, run, gate, and deploy any slice — "dbt for agents, terminal-native, local-first."

`ca` is porcelain over the existing APIs (`deploy`, the in-memory interpreter, `validate`, the projection→Langfuse export); it adds no new runtime.

## Install

```bash
pip install 'composable-agents[cli]'        # the `ca` command (pulls Typer; core stays PyYAML-only)
```

Run `ca` from a directory that contains your agents. With no config it auto-discovers; everything else is optional.

## The module

An **agent** is a top-level `@flow`-decorated function or an `Agent(...)` instance. `ca` finds them two ways:

- **AST scan (no import):** finds `@flow`/`Agent(...)` and the cross-`@flow` call edges for `ls`/`show`/`graph`/selection — fast, no side effects.
- **Subprocess resolve (on demand):** imports your module in an isolated process to produce the runnable IR only when a verb needs it (`run`, `lint`, `deploy`).

### Optional config

`[tool.ca]` in `pyproject.toml`, overridden by a sibling `ca.toml` when present:

```toml
[tool.ca]
src     = ["agents", "examples"]      # discovery roots (default: the current package)
exclude = ["examples/scratch_*.py"]

[tool.ca.tags]                         # tag agents for tag: selection
triage = ["support"]

[tool.ca.gates]
fail_severity = "error"                # default gate threshold for `ca lint`

[tool.ca.env.staging]                  # deploy/run targets (see "Outer loop")
temporal_address   = "temporal.example:7233"
temporal_namespace = "default"
task_queue         = "ca-staging"
cas                = "s3://my-bucket/ca"   # local envs default to .ca/cas (LocalDirCAS)
langfuse_host      = "https://cloud.langfuse.com"
```

A `local` environment always exists implicitly (LocalDirCAS at `.ca/cas`, no Temporal).

## Commands

| Command | What it does |
|---|---|
| `ca ls [SEL]` | List agents (name · kind · tags). |
| `ca show <agent>` | One agent: kind, source location, tags, cross-agent calls. |
| `ca graph [SEL]` | The cross-agent dependency DAG as Graphviz DOT. |
| `ca run <agent> [--input JSON] [--env]` | Execute locally and stream the terminal trace tree (or run against an env). |
| `ca lint [SEL] [--fail-severity]` | Structural validation; named diagnostics with severity gating. |
| `ca test [SEL] [--dry-run]` | Run `pytest` for the selected agents (matched by name via `-k`). |
| `ca trace <run-id>` | Render a cached run's trace tree and print its Langfuse deep link. |
| `ca doctor` | Preflight: discovery, git, Langfuse, Temporal. |
| `ca deploy [SEL] --env <name>` | Freeze → publish bundle to the env CAS → record in the deploy ledger. |
| `ca status [SEL] --env <name>` | Show what's deployed where + drift (exit 3 on drift). |

Every `[SEL]` accepts the selection grammar below.

## Selection grammar

The same grammar drives every verb:

| Form | Selects |
|---|---|
| `triage` | an agent by name |
| `tag:support` | all agents carrying a tag |
| `path:agents/*.py` | agents defined under a path glob |
| `state:modified` | agents whose source changed vs git `HEAD` (or `--state <ref>`) |
| `result:fail` | agents whose last local run failed |
| `a b` | union (space) |
| `a,b` | intersection (comma) |
| `--exclude EXPR` | subtract a set |
| `+triage` | `triage` + everything it calls (upstream / dependencies) |
| `triage+` | `triage` + everything that calls it (downstream / dependents) |
| `+triage+` | both directions |
| `2+triage` / `triage+2` | depth-bounded upstream / downstream |
| `@triage` | `triage`, its downstream closure, and the upstream of that closure |

Graph operators compose with any base, e.g. `+tag:support` (upstream of every `support` agent) and `ca test state:modified` (Slim-CI: test only what changed).

## Inner loop — local

```bash
ca run triage --input '"TICKET-42"'
```
```
└─ seq#12 [ok]
   └─ seq#9 [ok]
      ├─ call#0 [ok] $1.0000      ← a @tool call
      └─ think#3 [ok] $2.0000     ← a think() reasoner, with cost

output: {"reply": "..."}
```

The tree renders directly from in-memory projection events — fully offline. Runs are cached under `.ca/runs/` so `ca trace <run-id>` can re-render them and `result:fail` can select the failures.

## Gates

`ca lint` lowers each selected agent to IR and runs the structural validator, reporting named diagnostics (`CYCLE`, `UNFROZEN_CALL`, `UNKNOWN_PURE`, …) at `error`/`warning`. `--fail-severity` decouples *what is reported* from *what fails the build*:

- exit `0` — clean (or all findings below the threshold)
- exit `1` — findings at/above `--fail-severity`
- exit `2` — usage/resolve error

`ca test` runs `pytest` scoped to the selected agents (`-k`), so `ca test +triage` exercises an agent and its dependencies.

## Outer loop — deploy / status / run --env

`ca` adds a **deploy ledger** over the existing freeze/publish plumbing — the record of what is deployed where, which does not otherwise exist.

```bash
ca deploy triage --env staging
```
- freezes the agent (`deploy(..., strict=False)`, minting a content-addressed `artifact_hash`),
- publishes the bundle (frozen flow + manifest + pure sources) to the env's CAS (`LocalDirCAS` locally, `S3CAS` for `s3://`),
- appends a record to the **committed** ledger `.ca/deploys/<env>.json` (artifact hash + frozen IR + timestamp — self-describing).

```bash
ca status --env staging        # triage  clean   sha256:3f14bac…     (exit 0)
                               # triage  drift   sha256:…            (exit 3, after a source change)
```
Drift = re-freeze the current source and compare its `artifact_hash` to the ledger.

```bash
ca run triage --env staging --input '"TICKET-42"'
```
replays the **deployed** artifact (never re-freezes drifted source): connects to the env's Temporal and runs the frozen flow on its task queue via `run_flow`.

The ledger lives in git (`.ca/deploys/` is tracked); `.ca/runs/` and `.ca/cas/` are ignored. Immutable, content-addressed artifacts make rollback a pointer swap.

> **Status:** `--env local` (deploy/status/run) is local-only and needs no extra services. `run --env <cloud>` (Temporal) and S3 publishing require the `temporal` / `store` extras and live infrastructure.

## See also

- [Cheat-sheet](cheatsheet.md) — the authoring surfaces `ca` operates on.
- [Deploy to Temporal](deploy-temporal.md) / [Kubernetes](deploy-kubernetes.md) — the worker that executes deployed flows.
