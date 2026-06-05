# Documentation

New here? Read [getting-started.md](getting-started.md), then [concepts.md](concepts.md).

## Start here

- [Getting started](getting-started.md) — install the package, run a keyless local agent, and understand the first deploy path.
- [Examples](examples.md) — runnable examples that show the facade, approvals, budgets, and lower-level combinators.

## Understand it

- [Concepts](concepts.md) — the core model: typed flows, frozen IR, shape analysis, capabilities, and projection.
- [Capabilities and safety](capabilities-and-safety.md) — deny-by-default grants, approval gates, race admission, and bounded authority.
- [Deploy to Temporal](deploy-temporal.md) — durable execution, workers, activities, guarded Temporal imports, and deployment artifacts.

## Reference

- [Specification](SPEC.md) — the normative specification and conformance contract.
- [Typed flow design](design/typed-flow.md) — design rationale for the typed authoring surface.
- [Algebra sketch](design/algebra.hs) — algebraic model for the flow calculus.
- [Claude Managed Agents as a runtime](design/cma-runtime.md) — design note (proposal): a CMA backend for the `app` node, with the capability manifest projected as custom tools.

## Contribute

- [Contributing](../CONTRIBUTING.md) — development setup, CI checks, golden corpus rules, and pull request expectations.
