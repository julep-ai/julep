# Documentation

New here? Read the repository [README](../README.md), then
[AUTHORING.md](AUTHORING.md) and [concepts.md](concepts.md).

## For the team

- [Team guide](team-guide.md) — internal orientation for engineers authoring agents and flows: setup, the day-to-day authoring loop, which surface to use, and where to get help.
- [Cheat-sheet](cheatsheet.md) — dense quick reference for the `@flow` surfaces, registration, `deploy`/`dry_run`, the `Agent` facade, combinators, and the CLI.
- [Gotchas & FAQ](gotchas.md) — the recurring traps (define-time vs runtime, determinism, capability denials, dev-vs-strict, the PEP 723 footgun) and how to get unstuck.

## Start here

- [Getting started](getting-started.md) — install the package, run a keyless local agent facade, and understand the first deploy path.
- [Authoring guide](AUTHORING.md) — the `@flow` surfaces, determinism contract, and define-time diagnostics.
- [Examples](examples.md) — runnable examples that show `@flow`, the facade, approvals, budgets, and lower-level combinators.

## Understand it

- [Concepts](concepts.md) — the core model: typed flows, frozen IR, shape analysis, capabilities, and projection.
- [Capabilities and safety](capabilities-and-safety.md) — deny-by-default grants, approval gates, race admission, and bounded authority.
- [Dispatch boundary](dispatch-boundary.md) — what belongs in a flow vs. the dispatch layer.
- [Provider resilience](provider-resilience.md) — deterministic model fallback chains, error taxonomy, and per-provider circuit breakers at the `LlmCaller` seam.
- [Deploy to Temporal](deploy-temporal.md) — durable execution, workers, activities, guarded Temporal imports, and deployment artifacts.
- [Deploy on Kubernetes](deploy-kubernetes.md) — containerized workers via `composable-agents worker`, SIGTERM drain, health probes, and KEDA autoscaling on task-queue backlog.
- [Deploy on DBOS](deploy-dbos.md) — durable flows and agent loops on Postgres via dbos-transact.

## Reference

- [Specification](SPEC.md) — the normative specification and conformance contract.
- [Typed flow design](design/typed-flow.md) — design rationale for the typed authoring surface.
- [Algebra sketch](design/algebra.hs) — algebraic model for the flow calculus.
- [Claude Managed Agents as a runtime](design/cma-runtime.md) — as-built (v1, experimental): a CMA backend for the `app` node (`Agent.run_on_cma` / `CMAAgentEnv`), with the capability manifest projected as custom tools and an experimental HTTP client behind the `cma` extra.

## Contribute

- [Contributing](../CONTRIBUTING.md) — development setup, CI checks, golden corpus rules, and pull request expectations.
