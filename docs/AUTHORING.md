# Authoring Guide

`@flow` is the primary authoring surface for composable-agents. The decorator
runs the function once at definition time with `Handle` values. Registered
tools, registered pures, brains, and control helpers append graph steps instead
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
6. **Per-step policy.** Tool, pure, and brain steps can carry retry and timeout
   options. The frozen graph owns those options, so interpreter and durable
   backends see the same policy.

## Determinism Contract

Every callable used on a `Handle` must be registered by its raw function source
with `@tool` or `@pure`. Do not register wrappers, closures, or lambdas: pure
pins are source hashes of the raw function.

Application is define-time only. Calling a registered object on a `Handle`
builds graph structure; ordinary runtime work belongs in tool hands, pure
functions, or brain handlers.

Captured constants must be canonical JSON. Runtime handle captures must come
from the enclosing graph. Secret-shaped config is banned from captures and
static args; credentials belong in environment-backed tools or run principals,
never in the frozen flow artifact.

JSON constant kwargs on registered pures become `arr` static args and run as
`fn(value, **kwargs)`; JSON constant kwargs on tools and brains lower to
`std.bind` const-merges into the flowing record before the call.

Branch arms receive the branch subject by name. The remaining item parameter
of a `cond` or `switch` arm must match the subject handle label; other
enclosing values must be supplied as keyword captures. `each` bodies differ:
the item parameter is positional, while enclosing handles and constants are
captures.

Names are single-assignment graph fields derived from whole-function AST source
when available. Use `name=` as the explicit escape hatch; REPL and `exec`
contexts fall back to deterministic generated names.

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
