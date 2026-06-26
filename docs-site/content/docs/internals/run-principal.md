---
title: "Run Principal"
description: "Identity and authority for a running flow."
---

> Status: design draft 2026-06-10, decided with mem-mcp (option A1 of the
> adoption sketch: principal-by-reference threaded through workflow input;
> rejected: per-run client factories, tenant-in-payload envelopes). Companion
> to `docs/dispatch-boundary.md` (who may start a run) and
> `composable_agents/execution/effects.py` (the caller seams this extends).

## Thesis

Every effect caller in the framework is **process-global**: one `WorkerContext`
per worker, one `mcp_call` for every run that lands on it
(`execution/effects.py:36-70`). `McpCaller` receives
`(server, tool, value, idempotency_key)` — nothing identifies *on whose behalf*
the call is made. That is fine for single-tenant deployments and fatal for
multi-tenant ones: mem-mcp resolves every tool call against a store-scoped
token, and today the only channels for tenant identity are smuggling it inside
`value` (the framework owns that payload; it corrupts tool schemas, reply
schemas, and traces) or running a worker fleet per tenant.

The fix is a **run-scoped principal**: an opaque JSON object supplied at
dispatch, carried in workflow input, threaded by the `Env` into every effect
payload, and handed to the worker's callers as one extra argument. The
framework never interprets it. Two invariants make it safe:

1. **The principal is a reference, never a secret.** It names the tenant and a
   credential *reference* (e.g. `{"storeId": 413, "tokenRef": "cred_abc"}`);
   the worker resolves the actual bearer token from its own secret store at
   call time. Temporal workflow history is a durable, replayable, often
   exported record — bearer tokens must never enter it. A payload codec can
   encrypt history, but ref-passing removes the leak class instead of
   wrapping it.
2. **The principal is workflow input.** It is part of the run's arguments, so
   it is replay-stable by construction, identical across activity retries, and
   absent from the frozen artifact (freeze hashes and the golden corpus do not
   move).

## Surface

### Types

```python
# execution/effects.py
RunPrincipal = dict[str, Any]   # opaque to the framework; JSON-serializable

McpCaller = Callable[[str, str, Any, str, Optional[RunPrincipal]], Awaitable[Any]]
#                     (server, tool, value, idempotency_key, principal) -> result

LlmCaller  = Callable[[Reasoner, Any, Optional[RunPrincipal]], Awaitable[Any]]
#                     (reasoner, value, principal) -> result
```

Both callers gain the principal. Tools need it for tenant-scoped tool auth;
reasoners need it for per-tenant model routing, per-tenant API keys, and
per-tenant spend attribution. Same mechanism, one review.

**Back-compat:** `configure()` inspects the supplied callables' arity and wraps
2-/4-argument legacy callables so they keep working unchanged. New code should
take the principal positionally. The wrapper is registered once at `configure`
time, not per call.

### Dispatch

```python
await client.start_workflow(
    FlowWorkflow.run,
    FlowInput(flow_json=..., manifest_json=..., principal={"storeId": 413, "tokenRef": "cred_abc"}),
    ...,
)
# facade
agent.deploy(client, session_id=..., input=..., principal={...})
```

`principal` defaults to `None`; single-tenant deployments change nothing.
Every public entry point grows the keyword — `Agent.run` / `Agent.deploy`,
`Deployment.run()`, and the exported `run_flow` / `start_flow` helpers — so
raw-flow users never have to construct `FlowInput` by tool to set it.

### Threading

- `FlowInput` / `AgentInput` (harness) and the DBOS workflow inputs gain
  `principal: Optional[RunPrincipal]`.
- The `Env` carries it: `_TemporalEnv`, `DbosEnv`, and `InMemoryEnv` each hold
  the run's principal and stamp it into the effect payloads —
  `CallToolInput`, `InvokeReasonerInput`, and `CompilePlanInput` gain a
  `principal` field (`execution/effects.py:86-108`). `interpret()` takes it as
  a keyword argument for the in-memory path.
- `effects.run_call` passes it to `mcp_call` (and, for native tools, resolves
  it into transport headers via a worker-supplied
  `principal_headers: Callable[[RunPrincipal], dict[str, str]] | None` on
  `WorkerContext`; absent means no extra headers — native tools keep working).
- `effects.invoke_reasoner` passes it to the `LlmCaller`.
- **Every `continue_as_new` path copies it forward.** Both `FlowWorkflow` and
  `AgentWorkflow` segment via `continue_as_new`; the principal is part of the
  next segment's input, so a long-running run keeps its tenant identity across
  history segments. A segment restarting with `principal=None` when the run
  had one is a bug class the tests must pin.

### Propagation to children

Sub-flows (child `FlowWorkflow`) and sub-agents inherit the parent's principal
unchanged. The tenant does not change mid-run; there is deliberately **no API
to substitute a different principal on a `sub`** — that would be a privilege
boundary the capability model cannot see. If a flow genuinely spans tenants,
that is two runs at the dispatch layer.

`compilePlan` admits planner-emitted IR against the parent manifest as before;
plan execution reuses the run principal like any other node.

## Non-goals (this design)

- **Per-principal capability manifests.** Capabilities stay per-deployment.
  Tenant-conditional grants ("store 413 may not call X") are a dispatch-layer
  decision today; if a real need appears, a follow-up can key manifest
  selection on a principal field at workflow start. Noting it here so the
  field shape (`dict`, not a bare string) keeps that door open.
- **Framework-side credential resolution.** The framework never sees tokens.
  `tokenRef → token` is the worker's job (mem-mcp: fnox / `store_credentials`).
- **Principal-derived idempotency.** The activation `cid` already scopes per
  run; the worker may compound `(principal, cid)` if its backend needs
  per-tenant key namespaces.

## Failure semantics

A worker that requires a principal and receives `None` must fail fast with a
typed, non-retryable error (the existing policy-error envelope; no silent
single-tenant fallback). The framework adds `PrincipalRequired` to
`errors.py` for callers to raise; it joins `CapabilityDenied` et al. in the
non-retryable class list in the retry policy.

## Touch set

| File | Change |
|---|---|
| `execution/effects.py` | `RunPrincipal`, widened caller signatures + arity shim in `configure`, `principal` on `CallToolInput`/`InvokeReasonerInput`/`CompilePlanInput`, `principal_headers` on `WorkerContext` |
| `execution/interpreter.py` | `interpret(..., principal=None)`, `InMemoryEnv` carries + stamps it |
| `execution/harness.py` | `FlowInput`/`AgentInput` field, `_TemporalEnv` stamping, child workflow propagation, `continue_as_new` carry-forward in both workflows |
| `execution/dbos_backend.py` | same for `DbosEnv` / `flow_workflow` / `ca_agent` |
| `errors.py` | `PrincipalRequired` |
| public entry points (`Agent.run` / `Agent.deploy`, `Deployment.run`, `run_flow` / `start_flow`) | `principal=` passthrough |
| `docs/SPEC.md` | §: run principal (input, opacity, no-secrets rule, child propagation) |
| `docs/dispatch-boundary.md` | dispatch owns principal minting |
| tests | arity shim; in-memory + Temporal + DBOS threading; child propagation; principal survives `continue_as_new` in flow and agent workflows; `PrincipalRequired` non-retryable; golden corpus unmoved |

Everything flows through the one effects seam, so the change is cross-cutting
but mechanical. The only design-bearing decisions are the two invariants above.

<!-- ported-by ca-docs-site: internals/run-principal -->
