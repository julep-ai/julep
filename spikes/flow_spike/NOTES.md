# Phase 2.A Spike Notes

## Faked Static Args

- `spike.assign_episode_id`, `spike.assign_source`, `spike.assign_summary`,
  `spike.assign_merged`, `spike.assign_liner`, `spike.assign_return_arg`,
  and `spike.assign_return_value` stand in for `std.assign(key)`.
- `spike.pluck_episode_id`, `spike.pluck_source`, `spike.pluck_summary`,
  `spike.pluck_merged`, `spike.pluck_liner`, `spike.pluck_return_arg`,
  and `spike.pluck_return_value` stand in for `std.pluck(key)`.
- `spike.merge_source_summary` and `spike.merge_merged_liner` stand in for a
  parameterized merge/pack site where the compiler needs to know which env
  fields to combine. A generic `spike.merge` is registered too, but the naive
  env-threaded lowering cannot use it for env-field pair merges without static
  args or a real pack primitive.
- The frontend now rejects labels unless both `spike.assign_<label>` and
  `spike.pluck_<label>` are already registered. That is intentionally
  burdensome: parameterized `std.assign(key)` / `std.pluck(key)` static args
  would remove the need to hand-register every env key.

## Compiler Friction

- Python does not expose assignment targets to the callee at define time. This
  spike uses caller source-line capture (`inspect` + `linecache` + `ast`) to map
  simple one-line assignments such as `summary = think(...)` to env labels.
  Its limits are real findings: multiline calls, complex targets, generated
  code, and no-assignment returns need deliberate handling in phase 5. For the
  no-assignment `return write_summary_surfaces(merged | liner)` shape, the spike
  emits generic temporary labels `return_arg` and `return_value`.
- Current IR primitive calls only return the primitive output. To keep the env
  around a tool or brain call, the spike emits an administrative
  `par(ident(), seq(pluck_*, primitive))` inside an otherwise sequential layer,
  followed by an `assign_*` pure. This is not inferred user parallelism; it is
  the env-preservation shim needed until static args / first-class std pures
  make `assign(key)` and `pluck(key)` cheap and regular.
- The naive compiler's uniform env discipline also leaves assign/pluck
  adjacencies on linear chains, for example `assign_source` followed by
  `pluck_source` before the `alt`. Phase 4's linear-chain fast path and liveness
  pruning should remove that accepted noise. This is distinct from branch-arm
  pure handling: a pure branch arm now lowers directly to `arr(pure_name)`,
  because wrapping it in assign-then-pluck was not something an expert would
  hand-write.
- `switch` can lower directly to `dsl.alt(select=..., cases=..., default=...)`.
  No nested binary-alt workaround is needed.
- Plain Python calls cannot be intercepted by the language when the callee just
  receives a `Handle`. The spike exposes `apply(fn, handle)` as the resolver
  that can reject unregistered callables; wrapped registered tools use that
  resolver so authored code still reads like `read_episode(episode_id)`.
- The episode happy path has no independent user-authored effect-fenced layers
  that would have parallelized under the planned compiler. The only `par` nodes
  in this spike are administrative env-carrying pairs with `ident()`.
