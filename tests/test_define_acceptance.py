from __future__ import annotations

from typing import Any

from julep import (
    CapabilityManifest,
    as_flow,
    cond,
    deploy,
    dsl,
    each,
    flow,
    pure,
    reschedule,
    switch,
    think,
    tool,
)
from julep.ir import SLEEP_TOOL, CallStep, NativeTool, Node, canonical_json
from julep.transforms import normalize_ids
from examples import episode_summary_flow as episode


def _canonical_ir(node: Node) -> str:
    return canonical_json(normalize_ids(Node.from_json(node.to_json())).to_json())


@pure("p53.pending")
def p53_pending(snapshot: dict[str, Any]) -> bool:
    return bool(snapshot["pending"])


@pure("p53.status")
def p53_status(result: dict[str, Any]) -> str:
    return str(result["status"])


@pure("p53.reschedule_status")
def p53_reschedule_status(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {"status": "awaiting_children", "store_id": snapshot["store_id"]}


@pure("p53.label_one")
def p53_label_one(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "cluster_id": payload["cluster_id"],
        "label": f"{payload['store_id']}:{payload['cluster_id']}",
    }


@pure("p53.tally_labels")
def p53_tally_labels(labels: list[dict[str, Any]]) -> dict[str, Any]:
    return {"labels": labels, "count": len(labels)}


@pure("p53.success")
def p53_success(result: dict[str, Any]) -> dict[str, Any]:
    return {"status": "success", "count": result["count"]}


@pure("p53.stale")
def p53_stale(result: dict[str, Any]) -> dict[str, Any]:
    return {"status": "stale", "count": result["count"]}


@tool(effect="read", idempotent=True)
def p53_read_store(store_id: str) -> dict[str, Any]:
    return {
        "store_id": store_id,
        "version": 1,
        "pending": store_id == "pending",
        "clusters": [{"cluster_id": "c1"}, {"cluster_id": "c2"}],
        "force_stale": store_id == "stale",
    }


@tool(effect="write", idempotent=True)
def p53_cas_write(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "stale_source" if payload["force_stale"] else "success",
        "count": payload["count"],
    }


def test_episode_summary_define_acceptance_matches_combinator_and_rollup() -> None:
    @flow
    def happy_path(source: dict[str, Any]) -> dict[str, Any]:
        summary = think(episode.SUMMARIZER, source)
        merged = source | summary
        liner = think(episode.ONE_LINER, merged)
        return episode.write_summary_surfaces(merged | liner)

    @flow
    def not_found(source: dict[str, Any]) -> dict[str, Any]:
        status = episode.not_found_status(source)
        return status

    @flow
    def summarize_one(episode_id: str) -> dict[str, Any]:
        source = episode.read_episode(episode_id)
        return cond(episode.episode_found, source, then=happy_path, orelse=not_found)

    @flow
    def batch(episode_ids: list[str]) -> dict[str, Any]:
        return each(
            summarize_one,
            episode_ids,
            max_parallel=2,
            reducer=episode.tally_summary_statuses,
        )

    expected_summarize_one = dsl.seq(
        dsl.call(episode.read_episode.name),
        dsl.arr("std.init", {"key": "source"}),
        dsl.arr("std.pack", {"fields": {"source": {"field": "source"}}}),
        dsl.par(
            dsl.ident(),
            dsl.seq(
                dsl.arr("std.pluck", {"key": "source"}),
                dsl.arr("episode_found"),
            ),
        ),
        dsl.arr("std.assign", {"key": "__branch__"}),
        dsl.alt(
            "std.branch_predicate",
            if_true=dsl.seq(
                dsl.arr("std.pack", {"fields": {"source": {"field": "source"}}}),
                dsl.par(
                    dsl.ident(),
                    dsl.seq(
                        dsl.arr("std.pluck", {"key": "source"}),
                        dsl.think(episode.SUMMARIZER),
                    ),
                ),
                dsl.arr("std.assign", {"key": "summary"}),
                dsl.par(
                    dsl.ident(),
                    dsl.arr("std.merge", {"fields": ["source", "summary"]}),
                ),
                dsl.arr("std.assign", {"key": "merged"}),
                dsl.arr("std.pack", {"fields": {"merged": {"field": "merged"}}}),
                dsl.par(
                    dsl.ident(),
                    dsl.seq(
                        dsl.arr("std.pluck", {"key": "merged"}),
                        dsl.think(episode.ONE_LINER),
                    ),
                ),
                dsl.arr("std.assign", {"key": "liner"}),
                dsl.par(
                    dsl.ident(),
                    dsl.arr("std.merge", {"fields": ["merged", "liner"]}),
                ),
                dsl.arr("std.assign", {"key": "merge_1"}),
                dsl.arr("std.pluck", {"key": "merge_1"}),
                dsl.call(episode.write_summary_surfaces.name),
            ),
            if_false=dsl.seq(
                dsl.arr("std.pluck", {"key": "source"}),
                dsl.arr("not_found_status"),
            ),
        ),
    )
    expected_batch = dsl.each(expected_summarize_one, max_parallel=2, reducer="tally_summary_statuses")

    assert _canonical_ir(batch.to_ir()) == _canonical_ir(expected_batch)

    episode.reset_store()
    result = deploy(
        batch,
        tools=episode.TOOLS,
        reasoners=[episode.SUMMARIZER, episode.ONE_LINER],
    ).dry_run(
        episode.EPISODE_BATCH,
        reasoners={
            episode.SUMMARIZER: episode._fake_summarizer,
            episode.ONE_LINER: episode._fake_one_liner,
        },
    )

    assert result.value["counts"] == {"success": 2, "stale_source": 1, "not_found": 1}


def test_store_consolidation_define_acceptance_golden_and_behavior() -> None:
    @flow
    def reschedule_arm(snapshot: dict[str, Any]) -> dict[str, Any]:
        return reschedule(snapshot, after_s=300)

    @flow
    def label_one(cluster: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
        payload = snapshot | cluster
        label = p53_label_one(payload)
        return label

    @flow
    def success(written: dict[str, Any]) -> dict[str, Any]:
        out = p53_success(written)
        return out

    @flow
    def stale(written: dict[str, Any]) -> dict[str, Any]:
        out = p53_stale(written)
        return out

    @flow
    def consolidate(snapshot: dict[str, Any]) -> dict[str, Any]:
        clusters = snapshot["clusters"]
        labels = each(
            label_one(snapshot=snapshot),
            clusters,
            max_parallel=3,
            reducer=p53_tally_labels,
        )
        write_input = snapshot | labels
        written = p53_cas_write(write_input, retries=3, retry_interval_s=1, backoff_rate=2)
        return switch(
            p53_status,
            written,
            cases={"success": success, "stale_source": stale},
        )

    @flow
    def store_flow(store_id: str) -> dict[str, Any]:
        snapshot = p53_read_store(store_id)
        return cond(p53_pending, snapshot, then=reschedule_arm, orelse=consolidate)

    ir = store_flow.to_ir()
    pures = [node.pure for node in ir.walk() if node.pure is not None]
    selectors = [node.select for node in ir.walk() if node.select is not None]
    calls = [node.step.tool.name for node in ir.walk() if getattr(node.step, "tool", None) is not None]

    assert "std.branch_predicate" in pures
    assert "std.branch_selector" in selectors
    assert "std.each_pack" in pures
    assert calls == [p53_read_store.name, SLEEP_TOOL, p53_cas_write.name]

    pending_arm = next(
        node.left for node in ir.walk() if node.pure == "std.branch_predicate" and node.left is not None
    )
    pending_calls = [
        node.step.tool
        for node in pending_arm.walk()
        if isinstance(node.step, CallStep)
    ]
    pending_pures = [node.pure for node in pending_arm.walk() if node.pure is not None]

    assert NativeTool(SLEEP_TOOL) in pending_calls
    assert "std.continue_with" in pending_pures

    deployment = deploy(
        store_flow,
        tools=[p53_read_store, p53_cas_write],
        capabilities=CapabilityManifest.from_dict(
            {
                "tools": [
                    {"name": p53_read_store.name, "effect": "read", "idempotency": "native"},
                    {"name": p53_cas_write.name, "effect": "write", "idempotency": "native"},
                    {"name": SLEEP_TOOL, "effect": "read", "idempotency": "native"},
                ],
            }
        ),
    )

    assert deployment.dry_run("ok").value == {"status": "success", "count": 2}
    assert deployment.dry_run("stale").value == {"status": "stale", "count": 2}


def test_bound_flow_to_ir_matches_plain_flowlike_for_one_runtime_param() -> None:
    @flow
    def with_context(item: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        merged = context | item
        out = p53_label_one(merged)
        return out

    bound = with_context(context={"store_id": "s1"})
    node = as_flow(bound).to_ir()
    expected_body = dsl.seq(
        dsl.par(
            dsl.ident(),
            dsl.arr("std.merge", {"fields": ["context", "item"]}),
        ),
        dsl.arr("std.assign", {"key": "merged"}),
        dsl.arr("std.pluck", {"key": "merged"}),
    )
    expected = dsl.seq(
        dsl.arr(
            "std.pack",
            {
                "fields": {
                    "item": {"input": True},
                    "context": {"const": {"store_id": "s1"}},
                }
            },
        ),
        dsl.seq(expected_body, dsl.arr("p53.label_one")),
    )

    assert _canonical_ir(node) == _canonical_ir(expected)
