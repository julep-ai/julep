# Merge notes

This repo merges the stronger parts of the two uploaded implementations.

Base chosen: `composable-serverless-agents-ts`, because its workspace split is the better long-term library shape:

- `@csa/core`: pure IR, DSL, freezing, validation, plan validation.
- `@csa/temporal`: Temporal runtime, activities, worker/deploy helpers, projection.
- `examples/research-review`: small runnable example.

Semantics ported from `composable-agents-ts`:

- Static and dynamic `eval_plan` are both supported.
- `compilePlan` returns a full `Plan`, not just a `Node`.
- Generated plans can carry their own manifest and grants.
- Race/hedge/quorum admission is enforced correctly.
- Race/hedge/quorum runtime behavior is implemented in the workflow interpreter.
- Subagent contracts include task queue, budget, and schema fields.
- Native tools must have capability entries and endpoints before freeze.
- Projection has full envelopes, append-only event writer, value-store spillover, and Postgres schema.
- Activity dependency injection is available through `createActivities(deps)`.
- Whole-session parallel context lowering preserves provenance with `ann.degradedFrom = 'par'`.

Improvements added during merge:

- npm workspace support, replacing the previous pnpm-only assumption.
- Workflow-safe core export at `@csa/core/workflow` to avoid importing Node crypto into workflows.
- Direct native endpoint invocation; no hidden `/invoke` suffix is appended.
- Compatibility aliases for old field names: `toolHash`/`frozenHash`, `combiner`/`strategy`, `hedgeMs`/`hedgeDelayMs`.
- More thorough node tests covering freeze, manifest hash, shape behavior, race admission, staged plans, and context lowering.

Verification performed before packaging:

```bash
npm install
npm run build
npm test
node examples/research-review/dist/deploy.js
```

All tests passed locally before the archive was created.
