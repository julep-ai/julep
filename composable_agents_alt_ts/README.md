# Composable Serverless Agents

A TypeScript framework scaffold for the P1-P4 plan:

- frozen MCP tool manifests at run/deploy boundary
- pure JSON IR with a shape lattice
- structural validation and plan validation
- serverless hands behind static tool contracts
- Temporal workflow harness for durable execution
- Postgres pomset projection for observability, replay-debug, and cost accounting

This repository is intentionally split into two packages:

- `@csa/core`: pure IR, DSL, shape analyzer, freeze, validation, capability manifest parsing, derived combinators.
- `@csa/temporal`: Temporal workflow/activities/deploy hooks and pomset projection adapters.

The core package is the keystone. It has no Temporal dependency and can be golden-tested across languages later.

## Runtime choice

This scaffold chooses TypeScript because the Temporal TypeScript SDK maps directly to the workflow shape in the plan, the DSL gets strong static types, and Node is the natural host for mixed HTTP + MCP client adapters.

Temporal workers still need to be persistent Node worker processes. Serverless hands are HTTP targets only.

## Install

```bash
npm install
npm run build
npm test
```

## Package map

```text
packages/core/src/
  types.ts              # IR, schemas, contracts, diagnostics
  shape.ts              # surfaceShape / closedShape / join semilattice
  freeze.ts             # MCP snapshot + overrides -> frozen IR + manifest
  validate.ts           # structural rules, schema edges, race admission
  plan.ts               # validatePlan for model-generated staged plans
  dsl.ts                # pipeline/parallel/critique/stage/escalate/etc.
  derived.ts            # race/hedge/quorum/mapN/review/humanGate helpers
  pure.ts               # named deterministic pure registry
  stable.ts             # deterministic stringify + workflow-safe hash
  hash.ts               # host-side SHA-256 hashing
  workflow.ts           # workflow-safe exports only
  index.ts

packages/temporal/src/
  workflows/run.ts      # deterministic IR interpreter
  activities.ts         # callHand / invokeBrain / compilePlan
  deploy.ts             # freeze + validate + Temporal client start helpers
  mcp.ts                # MCP snapshot adapter interface
  projection.ts         # pomset event writer
  interceptor.ts        # worker interceptor sketch
  worker.ts             # persistent worker entrypoint
  schema.sql            # append-only projection schema
```

## Minimal DSL example

```ts
import {
  Contract,
  brainFromCtx,
  call,
  critique,
  mcpCall,
  parallel,
  pipeline,
  subagent
} from '@csa/core';

const retrieve = parallel(
  call('retrieve_docs'),
  mcpCall('notion', 'search')
);

const drafter = brainFromCtx('prompts/drafter.ctx/');
const reviewer = subagent('reviewer', Contract.agent());

export const flow = pipeline(
  retrieve,
  critique(3, drafter, { stopPure: 'critiqueConverged' }),
  reviewer
);
```

## Capability manifest

```yaml
capabilities:
  tools:
    retrieve_docs:
      kind: native
      endpoint: https://retrieve.run.app/invoke
      effect: read
      idempotency: required
    notion/search:
      kind: mcp
      server: notion
      effect: read
      idempotency: native
    gmail/send:
      kind: mcp
      server: gmail
      effect: dangerous
      idempotency: none
      approval: required
  models:
    - anthropic/claude-*
  network:
    egress:
      - api.github.com
      - "*.run.app"
      - "*.lambda-url.*.on.aws"
mcp_servers:
  notion:
    url: https://mcp.notion.com/mcp
    pin_version: true
```

## What is implemented vs intentionally stubbed

Implemented in this scaffold:

- complete IR and typed DSL
- shape analysis
- frozen tool manifest generation from MCP snapshots and overrides
- conservative MCP hint defaults
- validation rules for core structure, `eval_plan`, named pures, `par` context degradation warnings, tool binding, and race/hedge/quorum admission
- staged plan validator
- Temporal workflow interpreter skeleton
- activity contracts for HTTP hands, MCP calls, brains, and planners
- pomset projection schema and writer interface
- golden-test-style examples

Stubbed with clear seams:

- concrete MCP client implementation: adapter interface is present, session-pool strategy is left for the host app
- concrete LLM/dotctx renderer: `BrainRuntime` interface is present
- schema subtyping: starter structural checker is conservative; replace with your preferred JSON Schema compatibility checker later
- interceptor completeness: included as a high-signal starting point, but production deployments should wire full worker and activity interceptors

## Architectural notes

Temporal should be the system of record for execution history and retry semantics. The pomset is a derived projection, not a recovery mechanism. Temporal TypeScript supports interceptors as middleware-like hooks around workflow/activity calls, but this scaffold writes projection events from activities by default to avoid duplicate emission. Temporal also supports Continue-As-New for long workflows to create a fresh event history while keeping the workflow identity chain intact; the `app` loop code exposes a policy hook for this.

MCP tool annotations are treated only as untrusted hints. The freeze step seeds default contracts from annotations, then capability overrides assert the real contract. Race-sensitive combinators reject unasserted `none` idempotency at deploy time.
