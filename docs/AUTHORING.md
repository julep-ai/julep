# Authoring Guide

`@flow` is the primary authoring surface for composable-agents. The decorator
runs the function once at definition time with `Handle` values. Registered
tools, registered pures, reasoners, and control helpers append graph steps instead
of doing runtime work; lowering goes through `composable_agents.dag` and the
compiler, then freezes to the same wire-format IR as the combinator kernel.

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
6. **Per-step policy.** Tool, pure, and reasoner steps can carry retry and timeout
   options. The frozen graph owns those options, so interpreter and durable
   backends see the same policy.

## Determinism Contract

Every callable used on a `Handle` must be registered by its raw function source
with `@tool` or `@pure`. Do not register wrappers, closures, or lambdas: pure
pins are source hashes of the raw function.

Application is define-time only. Calling a registered object on a `Handle`
builds graph structure; ordinary runtime work belongs in tool tools, pure
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
see [SPEC §6.5](SPEC.md#65-pureruntimerefs--published-runtime-identity).

A pure with no declared dependencies has no `envHash`. Its bundle manifest and
published artifact remain byte-identical to a pre-deps-as-data deployment.

### Dependency tiers

The supported WASI-wheel set is exactly `pydantic-core` and `regex`
(`composable_agents/execution/env_builder.py::SUPPORTED_WASI_WHEELS`). If every
declared dependency is in that set, the pure resolves to the wasm tier: publish
builds a pre-initialized wasm environment component, content-addresses it as
`envComponent`, records the corresponding `envHash`, and the worker resolves
that component before running the pure in the wasmtime sandbox.

An off-list dependency such as `numpy` has no curated WASI wheel. Such a pure
can run only on the native tier: a `uv`-managed subprocess in a worker venv.
Native tier is opt-in per pure. The pure name must be present in the
`CA_PURE_NATIVE_DEPS` allowlist at both publish/deploy and worker resolution.
Without that grant, publish fails closed and names the pure plus the offending
dependency; a worker refuses to register an off-list native-tier pure it has not
granted. Native-tier refs carry no `envHash` or `envComponent`; the venv is
built from the declared dependencies at the worker. For operator trust
boundaries, see [the wasm tier runbook](ops/wasm-tier-runbook.md).

### Warning: metadata placement is load-bearing

`register_pure` and bundle publishing capture pure source with
`inspect.getsource(fn)`. `getsource` returns text from the decorator line
through the function body. It does not include a module-top block.

Today, a module-top `# /// script` block is silently dropped from the captured
source. The bundle publishes as a no-dependency pure, with no `envHash`, and the
missing dependency fails late when the worker imports inside the wasm sandbox.
This is a fail-open footgun: deploy can pass because the import works in the
native host environment, then the wasm-tier run fails at import.

Place the metadata between the `@pure(...)` decorator and `def`, so it is inside
the captured source span:

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
traps on `stat()`. Reproducible vendored cp314 wheels are deferred. See
`TODOS.md` entries "S2 wasm-wheel e2e -- the skipped leg" and `FIXME(P4-1)` for
the current state.

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
`composable_agents.typed`; use it when typed composition is the clearer escape
hatch.

To promote a `@flow` definition to a named, split-deployable unit, lift it with
`as_flow(...)` first: `as_flow(my_flow).named("my-flow")` mints a durable ref,
and `.as_sub(queue=...)` marks it for per-component split deployment — the same
machinery the typed facade uses.

For a **long-lived, keep-messaging** agent (open once, send many messages, stream
events, thread state across turns), author a **session** with `scan`/`loop`/`@session`
and open it via `agent.open(...)`. Sessions reuse this same authoring surface for
each turn. See [Sessions](sessions.md).
