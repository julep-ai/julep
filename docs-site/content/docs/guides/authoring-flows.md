---
title: "Authoring Flows"
description: "How to use @flow to build define-by-construction DAGs: surfaces, determinism contract, branching, fan-out, and diagnostics."
---

`@flow` is the primary authoring surface for julep. It is
define-by-construction: you write ordinary Python, but registered tools, pures,
reasoners, branches, fan-out, and retry/timeout policy build a single-assignment
DAG at definition time. That DAG compiles through `julep.dag`,
respects effect fences, then freezes to the same finite `Node` IR used by the
lower-level combinator DSL and durable runtimes.

## Quick Start

Requires Python 3.12+, no provider key, no Temporal server.

From a source checkout:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

From PyPI:

```bash
python -m pip install --pre julep
```

Create `quickstart_flow.py`:

<!-- julep:doctest expect-output -->
```python
from typing import TypedDict

from julep import Reasoner, deploy, flow, pure, think, tool


class SupportReply(TypedDict):
    reply: str


@tool(effect="read", idempotent=True)
def lookup_ticket(ticket: str) -> dict[str, str]:
    return {
        "ticket": ticket,
        "queue": "billing",
        "summary": "Use the duplicate-charge runbook.",
    }


@pure("ticket_prompt")
def ticket_prompt(hit: dict[str, str]) -> dict[str, str]:
    return {"queue": hit["queue"], "context": hit["summary"]}


SUPPORT_REPLY = Reasoner(
    name="support_reply",
    model="anthropic:claude-haiku-4-5-20251001",
    system="Draft one concise support reply as JSON.",
    reply=SupportReply,
)


@flow
def triage(ticket: str) -> dict[str, str]:
    hit = lookup_ticket(ticket, retries=2, timeout_s=5)
    prompt = ticket_prompt(hit)
    answer = think(SUPPORT_REPLY, prompt, timeout_s=10)
    return hit | answer


def fake_support_reply(value: dict[str, str]) -> SupportReply:
    return {"reply": f"{value['queue']}: {value['context']}"}


deployment = deploy(triage, tools=[lookup_ticket], reasoners=[SUPPORT_REPLY])
result = deployment.dry_run(
    "Customer was charged twice.",
    reasoners={"support_reply": fake_support_reply},
)

print(result.value)
print(deployment.surface_shape.value)
```

```text
{'ticket': 'Customer was charged twice.', 'queue': 'billing', 'summary': 'Use the duplicate-charge runbook.', 'reply': 'billing: Use the duplicate-charge runbook.'}
Dataflow
```

Run it:

```bash
python quickstart_flow.py
```

`@flow` ran `triage(...)` once at import time with `Handle` values. The tool,
pure, and reasoner calls appended DAG steps; `hit | answer` lowered to
`std.merge`; `deploy(...)` froze the tool and reasoner surface; `dry_run(...)`
executed locally with in-memory handlers.

## The Six Surfaces

1. **Step application.** Call registered tools, registered pures, `think(...)`,
   or another `@flow` with a `Handle` to append a step. Step calls accept
   execution options such as `retries=`, `retry_interval_s=`, `backoff_rate=`,
   and `timeout_s=`.
2. **Record dataflow.** `left | right` lowers to `std.merge`, and
   `record["key"]` lowers to `std.pluck`.
3. **Branching.** `cond(predicate, subject, then=..., orelse=...)` handles
   binary branches; `switch(selector, subject, cases=..., default=...)` handles
   multiway status branches.
4. **Fan-out and captures.** `each(body, items, max_parallel=..., reducer=...)`
   runs one body per item. The body item parameter is positional and may be
   named independently from the list-valued handle. Other enclosing values are
   captured explicitly by keyword.
5. **Reschedule.** `reschedule(state, after_s=..., mark=...)` owns a terminal
   continuation: optional dirty-mark tool, reserved `__sleep__`, then
   `std.continue_with`.
6. **Per-step policy.** Tool, pure, and reasoner steps can carry retry and
   timeout options. The frozen graph owns those options, so the interpreter and
   durable backends see the same policy.

## Authoring Model

A `@flow` function must have at least one parameter and must return a `Handle`;
the returned handle becomes the flow output.

Inside `@flow`, direct calls are allowed only for registered objects:

- `@tool(...)` functions from `julep.tool`
- `@pure(...)` functions from `julep.pure`
- other `@flow` definitions
- `think(...)`, `cond(...)`, `switch(...)`, `each(...)`, and `reschedule(...)`

Tool, pure, and reasoner steps accept these define-time step options:

<!-- julep:doctest skip -->
```python
step = lookup_ticket(ticket, name="hit", retries=2, retry_interval_s=1, backoff_rate=2, timeout_s=5)
```

`retries=` lowers to `Ann.max_attempts`; `timeout_s=`,
`retry_interval_s=`, and `backoff_rate=` lower to the corresponding `Ann`
fields in the frozen IR. `name=` controls the single-assignment output name.

Do not branch or iterate on a `Handle` with Python control flow. These are
define-time errors:

<!-- julep:doctest skip -->
```python
if hit:          # use cond(...)
    ...

for item in xs:  # use each(...)
    ...
```

Use record dataflow instead:

<!-- julep:doctest skip -->
```python
queue = hit["queue"]      # std.pluck
combined = hit | answer   # std.merge; later dictionaries win
```

## Tools, Pures, and Reasoners

Native tools are Python callables wrapped by `@tool`; their type hints become
input/output schemas where the built-in mapper can infer them. Allowed `effect=`
strings are `"read"`, `"write"`, `"external"`, and `"dangerous"`.
`idempotent=True` marks the tool as `Idempotency.NATIVE`.

Pures are deterministic workflow-side functions. They must not do IO, read
clocks, or depend on mutable globals.

<!-- julep:doctest skip -->
```python
@pure("route.is_billing")
def is_billing(hit: dict[str, str]) -> bool:
    return hit["queue"] == "billing"
```

Reasoners are registered by name and called with `think(name, handle)`. For
local `dry_run`, pass `reasoners={"name": fake_fn}` where `fake_fn(value)` returns
the model-shaped value.

## Branching and Fan-Out

Use `cond(pred, subject, then=..., orelse=...)` for binary branching and
`switch(selector, subject, cases={...}, default=...)` for multiway branching.
The predicate or selector must be a registered `Pure` or pure name. Branch arms
receive the subject by name, so the remaining arm parameter must match the
subject handle label; pass other values as keyword captures.

For record-field routing, use the explicit `switch(...)` form when you want to
name the selector yourself, or `switch_on(subject, key=...)` when the branch key
is just one field of the subject record. In both forms below, the branch subject
handle is named `req`, so each arm keeps a `req` parameter and captures the
separate `team_context` handle by keyword before merging it into the flowing
input. JSON constants in branch arms should be wrapped in a one-parameter arm;
`each(...)` is the helper that accepts JSON closure captures directly.

<!-- julep:doctest expect-output -->
```python
from julep import deploy, flow, pure, switch, switch_on


@pure("authoring_action_selector")
def action_selector(req: dict[str, object]) -> str:
    return str(req["action"])


@pure("authoring_team_context")
def team_context_for_arm(req: dict[str, object]) -> dict[str, object]:
    team_context = req["team_context"]
    assert isinstance(team_context, dict)
    return team_context


@pure("authoring_assign_review")
def assign_review(payload: dict[str, object]) -> dict[str, object]:
    return {"route": "review", "team": payload["team"], "order_id": payload["order_id"]}


@pure("authoring_assign_auto")
def assign_auto(payload: dict[str, object]) -> dict[str, object]:
    return {"route": "auto", "team": payload["team"], "order_id": payload["order_id"]}


@flow
def review(req: dict[str, object], team_context: dict[str, object]) -> dict[str, object]:
    payload = req | team_context
    return assign_review(payload)


@flow
def auto(req: dict[str, object], team_context: dict[str, object]) -> dict[str, object]:
    payload = req | team_context
    return assign_auto(payload)


@flow
def route_explicit(req: dict[str, object]) -> dict[str, object]:
    team_context = team_context_for_arm(req, name="team_context")
    return switch(
        action_selector,
        req,
        cases={
            "review": review(team_context=team_context),
            "auto": auto(team_context=team_context),
        },
        default=auto(team_context=team_context),
    )


@flow
def route_sugar(req: dict[str, object]) -> dict[str, object]:
    team_context = team_context_for_arm(req, name="team_context")
    return switch_on(
        req,
        key="action",
        cases={
            "review": review(team_context=team_context),
            "auto": auto(team_context=team_context),
        },
        default=auto(team_context=team_context),
    )


payload = {"order_id": "ret-100", "action": "review", "team_context": {"team": "returns"}}
print(deploy(route_explicit, tools=[]).dry_run(payload).value)
print(deploy(route_sugar, tools=[]).dry_run(payload).value)
```

```text
{'route': 'review', 'team': 'returns', 'order_id': 'ret-100'}
{'route': 'review', 'team': 'returns', 'order_id': 'ret-100'}
```

Use `each(body, items, max_parallel=..., reducer=...)` for dynamic fan-out over a
runtime list. The body can be a `@flow`, a partially-bound `@flow`, or a raw
`Node` outside `@flow`.

`reschedule(...)` is the terminal owned-continuation helper. It lowers to an
optional mark tool, the reserved `__sleep__` tool, then `std.continue_with`.

## Determinism Contract

Every callable used on a `Handle` must be registered by its raw function source
with `@tool` or `@pure`. Do not register wrappers, closures, or lambdas: pure
pins are source hashes of the raw function.

Application is define-time only. Calling a registered object on a `Handle`
builds graph structure; ordinary runtime work belongs in tool functions, pure
functions, or reasoner handlers.

Captured constants must be canonical JSON. Runtime handle captures must come
from the enclosing graph. Secret-shaped config is banned from captures and
static args; credentials belong in environment-backed tools or run principals,
never in the frozen flow artifact.

JSON constant kwargs on registered pures become `arr` static args and run as
`fn(value, **kwargs)`; JSON constant kwargs on tools and reasoners lower to
`std.bind` const-merges into the flowing record before the call.

Branch arms receive the branch subject by name. The remaining item parameter
of a `cond` or `switch` arm must match the subject handle label; other
enclosing values must be supplied as keyword captures. `each` bodies differ:
the item parameter is positional, while enclosing handles and constants are
captures.

Names are single-assignment graph fields derived from whole-function AST source
when available. Use `name=` as the explicit escape hatch; REPL and `exec`
contexts fall back to deterministic generated names.

## Third-Party Dependencies on Pures (PEP 723)

A pure declares third-party dependencies with a PEP 723 inline-script-metadata
block in the captured pure source:

```python
# /// script
# dependencies = ["regex==2024.11.6"]
# requires-python = ">=3.11"
# ///
```

`dependencies` is parsed as sorted, de-duplicated PEP 508 requirement strings.
`requires-python`, when present, is reduced to the pinned Python major.minor
used for dependency environment identity. The dependency list, pinned
major.minor, and vendored base wasm component hash feed the pure's `envHash`;
see [SPEC §6.5](/docs/internals/specification#65-pureruntimerefs--published-runtime-identity).

A pure with no declared dependencies has no `envHash`. Its bundle manifest and
published artifact remain byte-identical to a pre-deps-as-data deployment.

### Dependency tiers

The supported WASI-wheel set is exactly `pydantic-core` and `regex`
([`julep/execution/env_builder.py::SUPPORTED_WASI_WHEELS`](https://github.com/julep-ai/julep-v2/blob/main/julep/execution/env_builder.py)). If every
declared dependency is in that set, the pure resolves to the wasm tier: publish
builds a pre-initialized wasm environment component, content-addresses it as
`envComponent`, records the corresponding `envHash`, and the worker resolves
that component before running the pure in the wasmtime sandbox.

An off-list dependency such as `numpy` has no curated WASI wheel. Such a pure
can run only on the native tier: a `uv`-managed subprocess in a worker venv.
Native tier is opt-in per pure. The pure name must be present in the
`JULEP_PURE_NATIVE_DEPS` allowlist at both publish/deploy and worker resolution.
Without that grant, publish fails closed and names the pure plus the offending
dependency; a worker refuses to register an off-list native-tier pure it has not
granted. Native-tier refs carry no `envHash` or `envComponent`; the venv is
built from the declared dependencies at the worker.

### Warning: metadata placement is load-bearing

`register_pure` and bundle publishing capture pure source with
`inspect.getsource(fn)`. `getsource` returns text from the decorator line
through the function body. It does not include a module-top block.

A module-top `# /// script` block is silently dropped from the captured source.
The bundle publishes as a no-dependency pure, with no `envHash`, and the
missing dependency fails late when the worker imports inside the wasm sandbox.
This is a fail-open footgun: deploy can pass because the import works in the
native host environment, then the wasm-tier run fails at import.

Place the metadata between the `@pure(...)` decorator and `def`, so it is inside
the captured source span:

<!-- julep:doctest skip -->
```python
@pure("cad.demo.extract_emails.v1")
# /// script
# dependencies = ["regex==2024.11.6"]
# requires-python = ">=3.11"
# ///
def extract_emails(record: dict[str, Any]) -> dict[str, Any]:
    import regex

    text = str(record["text"])
    emails = regex.findall(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", text)
    return {"emails": sorted({email.lower() for email in emails})}
```

Do not place the block at module top. `FIXME(P4-2)` tracks the deferred fix:
rejecting undeclared third-party imports and/or supporting module-top metadata.

### Current WASI-wheel limit

The env-component build path is wired, and `envHash`/`envComponent` are real
wire identity. The end-to-end leg where a real WASI wheel imports and runs
inside the `--stub-wasi` wasm build is not closed yet: CPython import still
traps on `stat()`. Reproducible vendored cp314 wheels are deferred.

## Effect-Fenced DAG Compilation

`@flow` does not emit wire-format IR directly. It builds `dag.Graph` and
`dag.StepNode` values, then calls `dag.compile(...)`.

The compiler:

- topologically sorts steps and rejects cycles, unknown inputs, forward edges,
  reserved `__*__` output names, and output-name collisions;
- compiles straight-line chains to plain `seq(...)` without env-record shims;
- groups independent non-barrier steps into `par(...)` layers;
- treats branches and `each` bodies containing barriers as barriers;
- treats tool steps with `Effect.WRITE`, `Effect.EXTERNAL`, or
  `Effect.DANGEROUS` as barriers;
- inserts stable standard pures such as `std.init`, `std.pluck`, `std.merge`,
  `std.assign`, `std.collect`, `std.pack`, and `std.unpack` when an env record is
  needed for fan-in, branching, or closure conversion.

The effect fence governs ordering, not authorization. Authorization runs at
deploy through freeze, validate, capability enforcement, approval gates, and
race admission.

## Frozen IR

The frozen program is a finite `Node` tree. Core operators live in
`julep.kinds.Op`:

```text
prim ident arr seq par each alt iter_up_to eval_plan app loop
```

`prim` carries `CallStep`, `ThinkStep`, or `SubStep`. `Ann` carries optional
cost/risk/cache/effect metadata plus `timeout_s`, `max_attempts`,
`retry_interval_s`, `backoff_rate`, and `batchable`.

`freeze(...)` and `deploy(...)` serialize the authored tree as canonical JSON,
normalize node ids, bind every tool call to a frozen manifest entry, and include
registered pure source hashes and reasoner identities in the deployment artifact.
Typed wrappers, `Tool` objects, and Python callables do not enter `Node.to_json()`.

Use these inspection properties after `deploy(...)`:

<!-- julep:doctest skip -->
```python
deployment.flow_json
deployment.manifest_json
deployment.artifact_hash
deployment.surface_shape
deployment.diagnostics
deployment.prod_gap_summary()
```

For local iteration, `deploy(..., mode="dev")` returns a deployment with
would-block production diagnostics in `deployment.prod_gap`. Temporal
`Deployment.run(...)` rejects dev-mode deployments; dev mode is for local
iteration.

## Typed Composition Surface

The typed layer is an authoring wrapper over the same `Node` IR. It carries
Python type parameters while you build, then disappears before freeze.

<!-- julep:doctest skip -->
```python
from julep import tool
from julep.typed import Flow, as_flow, par, seq


@tool(effect="read", idempotent=True)
def fetch(ticket: str) -> dict[str, str]:
    return {"ticket": ticket}


@tool(effect="read", idempotent=True)
def classify(hit: dict[str, str]) -> dict[str, str]:
    return {**hit, "priority": "normal"}


@tool(effect="read", idempotent=True)
def fetch_account(ticket: str) -> dict[str, str]:
    return {"account": ticket}


pipeline = fetch >> classify
same_ir = seq(fetch, classify)
branches = par([fetch, fetch_account])
named = pipeline.named("support.triage.v1")

assert isinstance(as_flow(fetch), Flow)
print(named.local_name)
```

Verified typed APIs include `FlowLike.to_ir() -> Node`, `left >> right`,
`as_flow(x)`, `typed.seq(...)`, `typed.par(branches, join=None)`,
`typed.alt(pred, if_true, if_false)`, `typed.each(body, max_parallel=None,
reducer=None)`, `.named(ref)`, `.renamed(ref)`, `.as_sub(queue=None)`, and
`.local_name`.

`julep.flow_adapters` exposes explicit `Any` boundary helpers:
`as_type(T)` lowers to `ident()`, `expect(flow, T)` lowers to
`seq(flow, ident())`, and `any_edges(flow)` reports structural `app`,
`eval_plan`, and `think` boundaries visible in the IR.

To promote a `@flow` definition to a named, split-deployable unit, lift it with
`as_flow(...)` first: `as_flow(my_flow).named("my-flow")` mints a durable ref,
and `.as_sub(queue=...)` marks it for per-component split deployment — the same
machinery the typed facade uses.

## Define-Time Errors

Define-time diagnostics are part of the public API. They include source spans
when source is available and are intended to tell you how to rewrite the flow.

| Error family | Rewrite |
|---|---|
| Handle truthiness or iteration | Use `cond(...)`, `switch(...)`, or `each(...)`. |
| Unregistered callable on a handle | Decorate it with `@pure` or `@tool`, or call `think(...)`. |
| Unsaturated flow | Apply the flow to handles, bind captures by keyword, or pass it directly to `each`. |
| Rebinding or tuple-unpacking handle targets | Assign each step to one graph name, or pass `name=...`. |
| Unused `@flow` parameter | Remove it or use it; unused parameters are blocking errors. |
| Foreign-scope handle capture | Capture only handles from the enclosing graph. |
| Invalid, oversized, or secret-shaped capture | Keep captures small canonical JSON; move secrets to tools or principals. |
| Non-handle return | Return a handle produced by the authored graph. |

## Related Surfaces

The combinator kernel (`seq`, `par`, `alt`, `each`, `iter_up_to`, `stage`,
`app`, `sub`, and derived race-family helpers) is what `@flow` compiles to and
remains the wire-format ground truth. The typed facade lives in
`julep.typed`; use it when typed composition is the clearer escape
hatch.

For a long-lived, keep-messaging agent (open once, send many messages, stream
events, thread state across turns), author a session with `scan`/`loop`/`@session`
and open it via `agent.open(...)`. Sessions reuse this same authoring surface for
each turn. See [Sessions](/docs/guides/sessions).

## See Also

- [Concepts](/docs/concepts/model) — frozen IR, shape lattice, capabilities, projection.
- [Typed flow design](/docs/internals/typed-flow-calculus) — rationale and invariants for typed composition.
- [Specification](/docs/internals/specification) — normative wire-format and conformance rules.
- [Capabilities and safety](/docs/guides/capabilities-and-safety) — grants, approval gates, race admission.
- [Deploy to Temporal](/docs/deploy/temporal) — durable runtime and worker setup.
- [Contributing](/docs/development/contributing) — development setup, CI, and golden corpus rules.

<!-- ported-by julep-docs-site: guides/authoring-flows -->
