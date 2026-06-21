# Phase 2 Spike Learnings

## 1. Authoring verdict

The target sketch is still the right direction: source-shaped Python reads much
better than point-free combinators. The batch-A episode slice is already close:

```python
@flow
def happy_path(source):
    summary = think(SUMMARIZER, source)
    merged = source | summary
    liner = think(ONE_LINER, merged)
    return write_summary_surfaces(merged | liner)
```

The cluster slice confirms the same for fan-out, including closure conversion:

```python
@flow
def label_one(store_context, cluster):
    label_source = store_context | cluster
    label = think(LABEL_REASONER, label_source)
    keywords = think(KEYWORDS_REASONER, label_source)
    _ = label  # Consumed by spike.merge_label_source_keywords via the env.
    write_payload = label_source | keywords
    return write_cluster_label(write_payload)

BATCH = each(label_one(STORE_CONTEXT), max_parallel=3, reducer=tally_cluster_statuses)
```

Where it reads worse than the plan's target: `each(label_one(STORE_CONTEXT), ...)`
works, but because the spike has no `each(body, items_handle)` inside a parent
flow, the store snapshot is a module-level demo value instead of a handle read
earlier in the workflow. The product target still needs `each(label_one(snapshot),
clusters)` as a graph step.

The second independent step off `label_source` is authored as dataflow:

```python
label = think(LABEL_REASONER, label_source)
keywords = think(KEYWORDS_REASONER, label_source)
```

The naive compiler emits those sequentially. P3's effect-fenced layering should
put them in a `par(...)` layer because both are reads from the same source and
neither depends on the other.

## 2. Static args

Every fake static-arg site observed in phase 2:

- Pluck keys: `spike.pluck_episode_id`, `spike.pluck_source`,
  `spike.pluck_summary`, `spike.pluck_merged`, `spike.pluck_liner`,
  `spike.pluck_return_arg`, `spike.pluck_return_value`,
  `spike.pluck_store_context`, `spike.pluck_cluster`,
  `spike.pluck_label_source`, `spike.pluck_label`, `spike.pluck_keywords`,
  and `spike.pluck_write_payload`.
- Assign fields: the matching `spike.assign_*` family for all names above.
- Pack layouts: `spike.pack_label_one_store_context_cluster`.
- Unpack layouts: `spike.unpack_label_one_args`.
- Merge layouts: `spike.merge_source_summary`, `spike.merge_merged_liner`,
  `spike.merge_store_context_cluster`, and
  `spike.merge_label_source_keywords`.
- Bound tool config: not exercised as a tool config object; the bound store
  snapshot was faked by the pack pure instead.

Representative evidence:

```python
@pure("spike.pack_label_one_store_context_cluster")
def spike_pack_label_one_store_context_cluster(cluster: dict[str, Any]) -> dict[str, Any]:
    return {"store_context": dict(STORE_CONTEXT), "cluster": dict(cluster)}
```

```python
@pure("spike.merge_label_source_keywords")
def spike_merge_label_source_keywords(env: dict[str, Any]) -> dict[str, Any]:
    return {**env["label_source"], **env["label"], **env["keywords"]}
```

Conclusion: the planned IR shape is confirmed, with one correction. `arr` static
args need to cover not only a single key (`std.pluck("summary")`) but also named
layouts (`std.pack({"store_context": bound, "cluster": item})`) and multi-field
env projections (`std.merge(["label_source", "label", "keywords"])`). Call
`bound_args` remains the right place for durable, inspectable tool config, with
the same canonical-JSON and secret-ban rules.

## 3. Closure conversion

The spike surface is a partially applied `@flow`:

```python
BATCH = each(label_one(STORE_CONTEXT), max_parallel=3, reducer=tally_cluster_statuses)
```

Core lowering records the bound args, requires exactly one remaining item
parameter, then emits pack followed by the original body:

```python
def to_ir(self) -> Node:
    pack_name = self._pack_pure_name()
    _require_registered_pure(pack_name, f"partial flow {self.flow.name!r}")
    return dsl.seq(dsl.arr(pack_name), self.flow.to_ir())
```

Multi-parameter body compilation now starts from an unpack prologue:

```python
else:
    unpack_name = _unpack_name(graph.name)
    _require_registered_pure(unpack_name, f"flow {graph.name!r}")
    nodes = [dsl.arr(unpack_name)]
```

Correction to planned `std.pack`: it cannot be "just tuple/list pack" if traces
and env projections should remain readable. The useful packed value was a named
record:

```python
return {"store_context": dict(STORE_CONTEXT), "cluster": dict(cluster)}
```

The unpack side also needs named fields, not positional destructuring:

```python
return {
    "store_context": packed["store_context"],
    "cluster": packed["cluster"],
}
```

So P3 should specify `std.pack` as a named layout over item plus bound args. Key
order should be canonicalized for hashing, but user-facing field names must stay
source-derived.

## 4. Env threading

The naive compiler still emits the same env-preservation shim for every tool,
reasoner, and pure step:

```python
if step.kind in {"tool", "think", "pure"}:
    nodes.append(dsl.par(dsl.ident(), _step_flow(step)))
    nodes.append(dsl.arr(_assign_name(step.output.label)))
```

Field naming stayed source-derived: `label_source`, `label`, `keywords`,
`write_payload`, and `return_value` all came from Python assignment or return
context. Env plumbing stayed out of user-visible projections in authored code:
users wrote `label_source | keywords`, not `env["label_source"]`.

Liveness pruning will matter. The cluster slice had to collapse final payload
construction into one specialized merge:

```python
write_payload = label_source | keywords
```

and the registered pure had to reach all live fields:

```python
return {**env["label_source"], **env["label"], **env["keywords"]}
```

Without liveness-aware env threading, an intermediate merge assignment drops
older fields. The full compiler should preserve just the still-live fields
across layers and then prune them after the CAS write.

## 5. Reschedule

The real temporal rollup shape is:

```python
if child_event_total < rollup_input["event_count"]:
    await reschedule_rollup_dirty_step(
        granularity,
        store_id,
        bucket_start,
        last_error=(
            f"awaiting {child_granularity} summaries "
            f"({child_event_total}/{rollup_input['event_count']} events ready)"
        ),
        increment_error=True,
    )
```

Then it exits with an explicit status:

```python
return lf.tap({"status": "awaiting_children"})
```

Proposed authoring surface:

```python
return reschedule(
    after=delay(seconds=300),
    state=rollup_input,
    status={"status": "awaiting_children"},
    mark_dirty=reschedule_rollup_dirty,
)
```

Lowering sketch against existing primitives:

1. Run the optional `mark_dirty` tool/pure first. For mem-mcp this is the
   existing dirty-row write with `last_error="awaiting ..."`.
2. Run `delay(seconds=N)` if `after` is provided. This already lowers to the
   reserved `__sleep__` tool with `Ann.timeout_s`.
3. End the segment with `continue_with(state)` when the same flow should retry
   itself, or return `status` when an external dispatcher owns re-enqueue.

For `temporal_rollups.py`, the external dispatcher already re-enqueues dirty
buckets, so the first implementation should probably be `reschedule_dirty(...)`
as a terminal status helper rather than unconditional continuation. The common
IR substrate is still `delay(...)` plus `continue_with(...)` for workflows that
own their continuation.

No mock-level demo was added because a faithful demonstration would require a
new frontend primitive or a package-level helper. The written lowering is the
deliverable for this batch.

## 6. Define-time errors

Good catches:

```python
if len(remaining) != 1:
    raise ValueError(
        f"closure-converted each body {self.flow.name!r} must leave "
        f"exactly one unbound item parameter; remaining={remaining!r}"
    )
```

```python
if isinstance(result, BoundFlow):
    raise TypeError(
        "unsaturated @flow application cannot be returned or stored as "
        "runtime data; pass it directly to each(...) as a "
        "closure-converted body"
    )
```

```python
if label in self.labels:
    raise ValueError(
        f"label {label!r} is already bound in flow {self.name!r}; "
        "spike flow handles are single-assignment, so choose a new "
        "Python variable name for the derived value"
    )
```

Bad or incomplete catches:

- Missing glue pures still report internal pure names such as
  `spike.assign_missing`. That is useful for the spike but not acceptable as a
  product diagnostic.
- Multi-argument saturated subflows are rejected by the spike instead of lowered.
  The error is honest, but P5 should point at supported forms and the exact
  offending call site.
- Static-arg absence leaks into authoring constraints: users must know which
  labels have registered glue. P5 should hide this behind `std.*` pures.

## 7. P3/P4/P5 scope corrections

- P3: Add `each(body, items_handle, ...)` as a graph step, not only a top-level
  `FlowLike`. Closure conversion needs to pack bound handles read earlier in
  the workflow, not only module-level JSON values.
- P3: Specify `std.pack` as a named record layout with canonical static args,
  not positional packing.
- P3: Add a first-class multi-field projection/merge standard pure. The cluster
  payload needed `label_source`, `label`, and `keywords` in one deterministic
  payload build.
- P4: Liveness pruning is not optional polish. Without it, merge assignment can
  discard fields needed by a later payload build or keep too much context across
  fan-out histories.
- P4: Effect-fenced layering should parallelize the authored label/keywords
  diamond while preserving write ordering before the CAS tool.
- P5: Diagnostics must translate missing glue and closure-conversion failures
  into source-level messages. The current errors are useful for implementers,
  not enough for users.
- P5: Reschedule needs two surfaces: external-dispatch dirty marking that
  returns a status, and owned continuation that lowers to
  `delay(...) -> continue_with(state)`.
