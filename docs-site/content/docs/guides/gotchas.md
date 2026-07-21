---
title: "Gotchas & Troubleshooting"
description: "Recurring traps in julep authoring — define-time vs runtime, determinism, capability denials, dev vs strict, and failure triage."
---

Most errors surface as a define-time diagnostic with a `fix:` line — read that
first. Deeper background: [Authoring Guide](/docs/guides/authoring-flows) ·
[Capabilities & Safety](/docs/guides/capabilities-and-safety) ·
[Concepts](/docs/concepts/model).

## Define-time vs runtime

The single biggest source of confusion. A `@flow` body runs **once at define
time** to build a graph. The values you handle are `Handle`s, not data. A step
call (`my_tool(h)`, `think(...)`, `h["key"]`) **appends graph structure** — it
does not execute and does not return a real value you can branch on.

So this **fails** at define time:

```python
@flow
def bad(x):
    hit = lookup(x)
    if hit["found"]:          # ✗ Handle truthiness — there's no runtime value yet
        return think("a", hit)
    return think("b", hit)
```

Express control flow with graph constructs instead:

```python
@flow
def good(x):
    hit = lookup(x)
    return cond(found_pred, hit, then=branch_a, orelse=branch_b)   # registered pure predicate
```

Anything that needs a *runtime* value — looping over data, inspecting a result,
calling out — belongs **inside** a `@tool`, `@pure`, or reasoner handler, not in
the flow body.

Inside `@flow`, the allowed data operations are step calls, `h["key"]`, and
`h1 | h2`. Python `if`, `for`, equality, and attribute access are not runtime
data.

**Fix-table for common define-time errors:**

| Diagnostic | Rewrite |
|---|---|
| Handle truthiness or iteration | Use `cond(...)`, `switch(...)`, or `each(...)`. |
| Unregistered callable on a handle | Decorate with `@pure`/`@tool`, or call `think(...)`. |
| Unsaturated flow | Apply the flow to handles / bind captures by keyword / pass it to `each`. |
| Rebinding or tuple-unpacking a handle | Assign each step to one graph name, or pass `name=`. |
| Unused `@flow` parameter | Remove it or use it — unused params are **blocking**. |
| Foreign-scope handle capture | Capture only handles from the enclosing graph. |
| Invalid / oversized / secret-shaped capture | Keep captures small canonical JSON; move secrets out. |
| Non-handle return | Return a handle produced by the authored graph. |

Names come from the function's AST source when available; use `name=` as the
explicit escape hatch (REPL/`exec` contexts fall back to generated names).

### Example: branching with a registered pure

```python
from typing import Any
from julep import cond, flow, pure

@pure("ticket.is_large")
def is_large(ticket: dict[str, Any]) -> bool:
    return bool(ticket.get("large"))

@flow
def large(ticket: dict[str, Any]) -> dict[str, Any]:
    return ticket["details"]

@flow
def small(ticket: dict[str, Any]) -> dict[str, Any]:
    return ticket

@flow
def route(ticket: dict[str, Any]) -> dict[str, Any]:
    return cond(is_large, ticket, then=large, orelse=small)
```

Healthy: module import no longer raises `Handle truthiness`, iteration,
attribute, equality, or non-`Handle` return errors.

## Determinism contract

Every callable used on a `Handle` must be **registered by its raw function
source** with `@tool` or `@pure`. Pins are source hashes, so:

- **No wrappers, closures, or lambdas** as registered tools/pures. Register the
  raw `def`.
- **Captured constants must be canonical JSON** and small. Captured handles must
  come from the **enclosing** graph (no foreign-scope captures).
- **No secrets in the flow.** Credentials are banned from captures and static
  args — they belong in environment-backed tools or run principals, never in the
  frozen artifact.

Healthy: no `UNKNOWN_PURE`, `ARR_ARGS_NOT_JSON`, or `ARR_ARGS_SECRET`
diagnostics. Full rules: [Authoring Guide — Determinism Contract](/docs/guides/authoring-flows#determinism-contract).

## Capability denials

A tool the flow was not granted is **denied**, not routed somewhere surprising:

```text
- [CAP_TOOL_DENIED@$] error: tool 'srv/denied' is not granted
    --> app.py:42  (call(mcp("srv", "denied")))
    fix: Add this tool to the capability manifest's tools: allow-list, or remove the call.
```

Fix: grant it in `deploy(..., tools=[...] / reasoners=[...])` (or the capability
manifest for kernel flows), or remove the call.

A missing `grant` section means unconstrained; a present-but-empty section means
deny-all. Native tools use the tool name; MCP tools use `server/tool`.

```yaml
tools:
  - name: lookup_ticket
    effect: read
    idempotency: native
  - name: search/web
    effect: read
    idempotency: native
reasoners:
  - support_reply
mcp_servers:
  search: ">=1"
memory:
  - local
```

Healthy: no `CAP_TOOL_DENIED`, `CAP_MODEL_DENIED`, `CAP_SERVER_DENIED`, or
`CAP_MEMORY_DENIED`. See [Capabilities & Safety](/docs/guides/capabilities-and-safety).

## Approval gates for dangerous actions

A tool declared `effect="dangerous"` (or approval-required) **must sit behind**
`human_gate(...)`. Strict deploy refuses any ungated path to it — that's by
design, not a bug. Put the gate immediately before the effect:
`draft -> human_gate -> send`. See
[`examples/email_approval.py`](https://github.com/julep-ai/julep-v2/blob/main/examples/email_approval.py).

A gate in a sibling `par` branch or child `sub(...)` does not dominate the
parent path. Do not put dangerous or approval-required tools directly in
`app(tools=[...])` — that reports `CAP_APP_APPROVAL_TOOL`.

Healthy: strict deploy has no `APPROVAL_UNGATED`.

## Race-family contract failures

`race(...)`, `hedge(...)`, and `quorum(...)` cancel loser branches. Every branch
call must be read-only or asserted `native`/`required` idempotent; MCP hints
alone are untrusted.

| Code | Meaning | Fix |
|---|---|---|
| `RACE_UNASSERTED` | Branch call has no idempotency assertion | Add `idempotency: native` or `required` to the tool grant |
| `RACE_UNSAFE` | Branch call is write-effect | Remove it from the race or change the effect |
| `RACE_SUB` | Sub-flow contains unsafe calls | Fix the sub-flow or remove it from the race |

## Shape and schema mismatches

The shape order is:

```text
Shape.PIPELINE < Shape.DATAFLOW < Shape.BRANCHING < Shape.FEEDBACK < Shape.STAGED < Shape.AGENT
```

Use `surface_shape` for parent scheduling and `closed_shape` when `SubContract`
cost matters. `SEQ_TYPE` means the manifest proves the producer schema cannot
satisfy the consumer schema — fix tool schemas or insert a registered pure that
reshapes the value. `as_type(...)` and `expect(...)` are authoring-only retypes;
they insert no runtime validation.

Context-policy degradation warnings (`CTX_PAR_DEGRADED`, `CTX_EACH_DEGRADED`)
mean the flow will degrade to sequential execution — either accept that or change
`ContextPolicy`.

## dev mode vs strict

Strict is the **default** and is what production runs. While iterating, use
`deploy(..., mode="dev")` / `Agent(..., mode="dev")`: it keeps compiling/running
locally but **retains** the diagnostics strict prod would block on.

- `deployment.prod_gap_summary()` → exactly what strict prod would reject.
- `result.prod_gap` → same, on a run result.
- **Temporal stays prod-strict.** `Deployment.run(...)` rejects dev-mode
  deployments and `Agent.deploy(...)` uses the strict path — so "works in dev"
  does not mean "deploys." Clear the prod gap before shipping.

## Keyless default reasoner

If you build an `Agent` without `llm=`, it does **not** call a model. It uses a
keyless default reasoner that emits **one** `RuntimeWarning` and returns the
input unprocessed. That's intentional for keyless local iteration — but if your
agent "does nothing," check whether you forgot to wire `llm=`. For a real model,
pass a controller (or `make_local_reasoner()` with the `providers` extra).

## PEP 723 metadata placement

A pure declares third-party deps with a `# /// script` block. `register_pure`
captures source via `inspect.getsource`, which **only sees from the decorator
line through the function body** — *not* a module-top block.

A module-top block is **silently dropped**: the pure publishes as no-dependency,
deploy passes (the import works on the native host), then the **wasm-tier run
fails at import**. Place the block **between `@pure(...)` and `def`**:

```python
@pure("cad.extract_emails.v1")
# /// script
# dependencies = ["regex==2024.11.6"]
# requires-python = ">=3.11"
# ///
def extract_emails(record: dict) -> dict:
    import regex
    ...
```

Supported WASI wheels are exactly `pydantic-core` and `regex`. Off-list deps
(e.g. `numpy`) only run on the **native tier**, which is opt-in per pure via the
`JULEP_PURE_NATIVE_DEPS` allowlist at both publish and worker. Details:
[Authoring Guide — Dependencies](/docs/guides/authoring-flows#third-party-dependencies-on-pures-pep-723).

## Step options and output-name collisions

Step calls accept `name=`, `retries=`, `retry_interval_s=`, `backoff_rate=`, and
`timeout_s=`. `name=` must be unique within the graph and must not match
`__*__`.

Healthy: no output-name collision, no reserved-name error, and no
`RETRY_FIELD_*` diagnostic.

## Verify gates

Run the same checks CI runs before pushing
([CONTRIBUTING](https://github.com/julep-ai/julep-v2/blob/main/CONTRIBUTING.md#running-the-checks)):

```bash
ruff check julep
python -m mypy julep
python -m pytest -q
```

- Use **`python -m pytest`**, not bare `pytest`, so it runs against the project's
  interpreter and resolves the package correctly.
- The pure core must stay free of `temporalio`; only `julep/execution/`
  may import it. `mypy` and `ruff` must be clean and public APIs stay typed.
- Tests run both with Temporal **absent** and **present** — `HAVE_TEMPORAL`
  gates the runtime, and the authoring path must pass either way.

## "The golden hashes changed and CI is red"

`tests/golden/` is the cross-language wire-format contract. A moved pin means the
IR, manifest JSON, diagnostics, or shape projection changed. If that change was
**intentional**, regenerate and review the diff as part of the change:

```bash
python -m tests.golden.regenerate --update
```

If a pin moved and you didn't mean to change the wire format, **stop and
investigate** — something in the compile path shifted.
[Golden corpus rules →](https://github.com/julep-ai/julep-v2/blob/main/CONTRIBUTING.md#the-golden-corpus-is-a-contract)

---

## Full triage procedure

Use this sequence when a flow will not import, compile, deploy, or run.

### Prerequisites

- Python `>=3.12`.
- CLI installed (ships with the base install):

```bash
pip install --pre julep   # from PyPI
pip install -e .          # from a source checkout (contributors)
```

Healthy: `julep --help` lists commands.

- For failures that only appear on the durable path:

```bash
pip install --pre 'julep[temporal]'   # from PyPI
pip install -e '.[temporal]'                 # from a source checkout (contributors)
temporal server start-dev
```

Healthy: Temporal Web is reachable at `http://localhost:8233`.

- For source span pointers in raw combinator DSL nodes:

```bash
export JULEP_SOURCE_CAPTURE=1
```

### Step 1 — Reproduce the earliest failure boundary

```bash
python - <<'PY'
import importlib

importlib.import_module("your_agents_module")
print("import ok")
PY
```

Healthy: `import ok`. If this fails, fix define-time authoring before looking at
deploy or runtime.

### Step 2 — Render deploy diagnostics

Replace `FLOW`, `TOOLS`, and the capabilities file with the affected objects:

```bash
python - <<'PY'
from julep import CapabilityManifest, deploy, explain
from your_agents_module import FLOW, TOOLS

caps = CapabilityManifest.from_file("capabilities.yaml")
deployment = deploy(FLOW, tools=TOOLS, capabilities=caps, strict=False, mode="dev")
print(explain(deployment.diagnostics))
print(deployment.prod_gap_summary())
print(deployment.surface_shape.value)
print(deployment.artifact_hash)
PY
```

Healthy: `No diagnostics.`, `no prod gap`, expected shape, and an artifact hash.

### Step 3 — Inspect existing artifacts

If you already have frozen artifacts, inspect them without importing source:

```bash
julep artifact validate flow.json --manifest manifest.json
julep artifact inspect flow.json --manifest manifest.json --caps capabilities.yaml
julep artifact graph flow.json
```

Healthy: `validate` prints `No diagnostics.` and exits `0`.

### Step 4 — Lint via julep

```bash
julep lint +triage --fail-severity error
```

Healthy: exit `0`. Exit `1` means findings at/above threshold. Exit `2` means
discovery or resolve failed.

### Step 5 — Classify and fix

| Symptom or code | Boundary | Fix |
|---|---|---|
| `Handle truthiness`, iteration, equality | define-time | use `cond(...)`, `switch(...)`, or `each(...)` |
| `unregistered callable` | define-time | decorate with `@pure` / `@tool`, call `think(...)`, or call an `@flow` |
| unused parameter, non-`Handle` return, unsaturated flow | define-time | remove unused params, return a handle, bind captures |
| `ARR_ARGS_*`, secret-shaped value | define/validate | keep constants canonical JSON; move secrets to tools/principals |
| `SEQ_TYPE` | validate after freeze | align schemas or insert a registered pure adapter |
| `CAP_*_DENIED`, `CAP_VERSION_PIN` | capability gate | grant the ref or remove it |
| `APPROVAL_UNGATED`, `CAP_APP_APPROVAL_TOOL` | approval gate | add `human_gate(...)` on every path or remove the tool from `app(...)` |
| `RACE_UNASSERTED`, `RACE_UNSAFE`, `RACE_SUB` | race admission | assert read/idempotent contracts or remove cancellation |
| `CTX_PAR_DEGRADED`, `CTX_EACH_DEGRADED` | warning | expect sequential degrade or change `ContextPolicy` |

### Step 6 — Re-run and re-freeze

```bash
julep lint +triage --fail-severity error
julep run triage --input '"TICKET-42"'
```

Healthy: lint exits `0`; run streams a trace tree and prints `output:`.

```bash
julep artifact freeze flow.json snapshot.json --caps capabilities.yaml
```

Healthy: output includes `frozen_flow`, `manifest`, `diagnostics:`, and
`No diagnostics.`. Preserve the `artifact_hash`.

### Verification checklist

- Library: `deploy(FLOW, tools=TOOLS, capabilities=caps)` returns a strict
  `Deployment` without raising `ValidationError`.
- Local execution: `deployment.dry_run(input, reasoners={...})` returns the
  expected `.value` with deterministic fake reasoners.
- CLI: `julep lint <selector> --fail-severity error` exits `0`.
- Artifact: `julep artifact validate flow.json --manifest manifest.json`
  prints `No diagnostics.`.
- Temporal: the worker is ready, the workflow terminates, and `projection` has
  expected `events`, `costByShape`, and `pending`.

### Rollback

1. Do not patch `flow_json` or `manifest_json` by hand. Roll back authored
   source or select a previous frozen artifact.
2. Check whether current source drifted from the deployed artifact:

```bash
julep status triage --env staging
```

Healthy deployed state: `clean` and exit `0`. Drift exits `3`.

3. To keep serving the last known-good artifact, run against the deployed env
   instead of re-freezing drifted source:

```bash
julep run triage --env staging --input '"TICKET-42"'
```

4. For CAS/ledger deployments, rollback is selecting the previous immutable
   `artifact_hash` from the deploy ledger or CAS record. After the pointer swap,
   rerun `julep status triage --env staging` and a representative `julep run`.

### Escalation

Capture before escalating:

- First import traceback (if define-time failed); full
  `explain(deployment.diagnostics)` and `deployment.prod_gap_summary()`.
- `deployment.artifact_hash`, `deployment.flow_json`, `deployment.manifest_json`,
  redacted capability manifest, and `surface_shape` / `closed_shape`.
- `julep doctor`, `julep lint +triage --fail-severity error`,
  `julep status triage --env staging`, and `julep trace <run-id>` for failed local runs.
- Temporal worker logs, workflow history, `openGates`, and `projection`; in local
  dev, inspect Temporal Web at `http://localhost:8233`.
- Kubernetes worker env (`WORKER_CONTEXT_FACTORY`, `TEMPORAL_ADDRESS`,
  `TEMPORAL_NAMESPACE`, `TEMPORAL_TASK_QUEUE`, `WORKER_HEALTH_PORT`), `/healthz`,
  `/readyz`, and recent pod logs.

Escalate with the smallest reproducer that imports the affected `@flow`, the
capability manifest, and either the source module or the frozen IR/manifest pair.

<!-- ported-by julep-docs-site: guides/gotchas -->
