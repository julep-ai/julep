# The Dispatch Boundary

A frozen flow describes **processing**: what happens to a value once work has
begun. Everything that decides **when and whether** work begins lives outside
the IR, in the *dispatch layer* -- the thin code that hands an input to a
backend runner (`run_flow` on Temporal, `run_flow_dbos` on DBOS).

Outside the IR (dispatch-layer concerns):

| Concern | Why it stays outside | Where it lives |
|---|---|---|
| Schedules / cron | "When to start" is not part of the computation | Temporal Schedules, `@DBOS.scheduled`, your scheduler |
| Debounce / batching windows | Collapses *inputs* before any flow exists | `dbos.Debouncer`, signal-with-start patterns |
| Dedup / idempotent submission | Identity of a *run*, not of a step | Workflow ids (both engines dedupe per id) |
| Webhook / event triggers | Transport, auth, replay protection | Your HTTP layer |
| Queue/worker routing | Capacity management across replicas | Temporal task queues, DBOS queues + roles |
| Principal minting | *Who* a run acts for is decided before work begins | `principal=` on `run_flow` / `run_flow_dbos` / `Deployment.run` (SPEC §8.11) |

Inside the IR (processing concerns): sequencing, fan-out (`par`, bounded by
`ExecutionPolicy.max_parallel`), branching (`alt`), bounded loops
(`iter_up_to`), durable waits (`delay`, `human_gate`), staged plans, sub-flows,
budgets, and the capability surface the flow runs against (grants live in the
capability manifest frozen alongside the flow).

**Dispatch owns principal minting.** The run principal (an opaque
tenant/credential reference, never a secret) is supplied at dispatch as
workflow input; the IR never names a tenant, and the principal cannot change
mid-run -- children and continuation segments inherit it unchanged. A flow that
genuinely spans tenants is two runs at this layer.

**Continuation sits exactly on the boundary.** A flow ends with
`continue_with(next_input)` to say "the processing of *this* segment is done;
dispatch me again with that input." The flow never schedules itself -- the
runner does (`continue_as_new` on Temporal, a fresh workflow id per segment on
DBOS) -- so segment dispatch stays inspectable, deduplicable, and cancelable by
the same machinery as any other dispatch.

This split is what makes frozen flows engine-portable: a flow re-authored from
hand-rolled orchestration must move *only its processing* into the IR. If you
find yourself wanting a cron expression, a debounce window, or a dedup key
inside a flow, you have found dispatch -- keep it outside.
