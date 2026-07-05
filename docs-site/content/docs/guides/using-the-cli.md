---
title: "Using the julep CLI"
description: "Discover, run, lint, test, deploy, and trace a whole module of agents with one selection grammar."
---

`julep` is the developer-facing CLI for a **module of agents**. Where the lower-level plumbing CLI (`python -m julep.cli`) operates on frozen JSON artifacts, `julep` operates on your **Python source**: point it at a directory and it discovers every `@flow` and `Agent(...)`, treats each as a node in a cross-agent dependency graph, and gives you one selection grammar to inspect, run, gate, and deploy any slice — "dbt for agents, terminal-native, local-first."

`julep` is porcelain over the existing APIs (`deploy`, the in-memory interpreter, `validate`, the projection→Langfuse export); it adds no new runtime.

## Install

```bash
pip install --pre julep        # the `julep` command ships with the base install
```

Run `julep` from a directory that contains your agents. With no config it auto-discovers; everything else is optional.

## The module

An **agent** is a top-level `@flow`-decorated function or an `Agent(...)` instance. `julep` finds them two ways:

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
fail_severity = "error"                # default gate threshold for `julep lint`

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
| `julep ls [SEL]` | List agents (name · kind · tags). |
| `julep show <agent>` | One agent: kind, source location, tags, cross-agent calls. |
| `julep graph [SEL]` | The cross-agent dependency DAG as Graphviz DOT. |
| `julep run <agent> [--input JSON] [--env]` | Execute locally and stream the terminal trace tree (or run against an env). |
| `julep lint [SEL] [--fail-severity]` | Structural validation; named diagnostics with severity gating. |
| `julep test [SEL] [--dry-run]` | Run `pytest` for the selected agents (matched by name via `-k`). |
| `julep trace <run-id>` | Render a cached run's trace tree and print its Langfuse deep link. |
| `julep doctor` | Preflight: discovery, git, Langfuse, Temporal. |
| `julep deploy [SEL] --env <name>` | Freeze → publish bundle to the env CAS → record in the deploy ledger. |
| `julep status [SEL] --env <name>` | Show what's deployed where + drift (exit 3 on drift). |
| `julep chat <agent>` | Open a **local session** REPL: type a line, stream `Turn`/`Emit` events back, exit on `Closed`. |
| `julep trigger <agent> <event> [--channel]` | Send one event into a session and render the resulting emits. |
| `julep listen <agent> --forward-to URL` | Open a session and forward each emitted event to `URL` (HTTP POST). |

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

Graph operators compose with any base, e.g. `+tag:support` (upstream of every `support` agent) and `julep test state:modified` (Slim-CI: test only what changed).

## Inner loop — local

```bash
julep run triage --input '"TICKET-42"'
```
```
└─ seq#12 [ok]
   └─ seq#9 [ok]
      ├─ call#0 [ok] $1.0000      ← a @tool call
      └─ think#3 [ok] $2.0000     ← a think() reasoner, with cost

output: {"reply": "..."}
```

> `julep run` executes with **offline echo stubs** for tools and reasoners (each
> returns `{"output": <input>}`) so it never needs a key or network — it is for
> seeing the **trace tree and control flow**, not realistic values. For realistic
> local output, use `deployment.dry_run(input, reasoners={...})` with fake
> reasoners (see [Your First Flow](/docs/start/first-flow)). Registered `@pure`
> functions run for real in both.

The tree renders directly from in-memory projection events — fully offline. Runs are cached under `.ca/runs/` so `julep trace <run-id>` can re-render them and `result:fail` can select the failures.

## Gates

`julep lint` lowers each selected agent to IR and runs the structural validator, reporting named diagnostics (`CYCLE`, `UNFROZEN_CALL`, `UNKNOWN_PURE`, …) at `error`/`warning`. `--fail-severity` decouples *what is reported* from *what fails the build*:

- exit `0` — clean (or all findings below the threshold)
- exit `1` — findings at/above `--fail-severity`
- exit `2` — usage/resolve error

`julep test` runs `pytest` scoped to the selected agents (`-k`), so `julep test +triage` exercises an agent and its dependencies.

## Outer loop — deploy / status / run --env

`julep` adds a **deploy ledger** over the existing freeze/publish plumbing — the record of what is deployed where, which does not otherwise exist.

```bash
julep deploy triage --env staging
```
- freezes the agent (`deploy(..., strict=False)`, minting a content-addressed `artifact_hash`),
- publishes the bundle (frozen flow + manifest + pure sources) to the env's CAS (`LocalDirCAS` locally, `S3CAS` for `s3://`),
- appends a record to the **committed** ledger `.ca/deploys/<env>.json` (artifact hash + frozen IR + timestamp — self-describing).

```bash
julep status --env staging        # triage  clean   sha256:3f14bac…     (exit 0)
                               # triage  drift   sha256:…            (exit 3, after a source change)
```
Drift = re-freeze the current source and compare its `artifact_hash` to the ledger.

```bash
julep run triage --env staging --input '"TICKET-42"'
```
replays the **deployed** artifact (never re-freezes drifted source): connects to the env's Temporal and runs the frozen flow on its task queue via `run_flow`.

The ledger lives in git (`.ca/deploys/` is tracked); `.ca/runs/` and `.ca/cas/` are ignored. Immutable, content-addressed artifacts make rollback a pointer swap.

> **Status:** `--env local` (deploy/status/run) is local-only and needs no extra services. `run --env <cloud>` (Temporal) and S3 publishing require the `temporal` / `store` extras and live infrastructure.

## Sessions — chat / trigger / listen

These verbs open a **session** (a long-lived, keep-messaging agent) on the local backend over a selected agent:

```bash
julep chat support-agent                       # REPL: each line is a message; Turn/Emit events stream back
julep trigger support-agent '{"text": "hi"}'   # one-shot: send one event, render the reply, close
julep listen support-agent --forward-to https://example.com/hook   # forward emitted events to a URL
```

`julep chat`/`julep listen` read stdin off the event loop so events stream concurrently; `julep trigger --channel` validates the channel against the session's input channel up front. Full session model (authoring, the `SessionEvent` stream, and the Temporal/CMA backends): **[Sessions](/docs/guides/sessions)**.

## See also

- [Sessions](/docs/guides/sessions) — long-lived agents the `chat`/`trigger`/`listen` verbs drive.
- [Cheat-sheet](/docs/reference/cheatsheet) — the authoring surfaces `julep` operates on.
- [Deploy to Temporal](/docs/deploy/temporal) / [Kubernetes](/docs/deploy/kubernetes) — the worker that executes deployed flows.

## See also

- [`julep` CLI reference](/docs/reference/ca-cli) — every subcommand, flag, and the full selection grammar.
- [Operations](/docs/deploy/operations) — operational runbooks for deploy, status/drift, and tracing a failing run in production.

<!-- ported-by ca-docs-site: guides/using-the-cli -->
