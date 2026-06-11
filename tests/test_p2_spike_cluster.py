from __future__ import annotations

import pytest

from composable_agents import deploy
from composable_agents import dsl
from composable_agents.ir import Node, canonical_json
from composable_agents.transforms import normalize_ids
from spikes.flow_spike import cluster_slice
from spikes.flow_spike.core import each, flow, think


def _canonical_ir(node: Node) -> str:
    return canonical_json(normalize_ids(Node.from_json(node.to_json())).to_json())


def _hand_written_spike_cluster_ir() -> Node:
    label_one_body = dsl.seq(
        dsl.arr("spike.unpack_label_one_args"),
        dsl.arr("spike.merge_store_context_cluster"),
        dsl.arr("spike.assign_label_source"),
        dsl.par(
            dsl.ident(),
            dsl.seq(
                dsl.arr("spike.pluck_label_source"),
                dsl.think(cluster_slice.LABEL_BRAIN),
            ),
        ),
        dsl.arr("spike.assign_label"),
        dsl.par(
            dsl.ident(),
            dsl.seq(
                dsl.arr("spike.pluck_label_source"),
                dsl.think(cluster_slice.KEYWORDS_BRAIN),
            ),
        ),
        dsl.arr("spike.assign_keywords"),
        dsl.arr("spike.merge_label_source_keywords"),
        dsl.arr("spike.assign_write_payload"),
        dsl.par(
            dsl.ident(),
            dsl.seq(
                dsl.arr("spike.pluck_write_payload"),
                cluster_slice.write_cluster_label.to_ir(),
            ),
        ),
        dsl.arr("spike.assign_return_value"),
        dsl.arr("spike.pluck_return_value"),
    )
    label_one = dsl.seq(
        dsl.arr("spike.pack_label_one_store_context_cluster"),
        label_one_body,
    )
    return dsl.each(
        label_one,
        max_parallel=3,
        reducer="tally_cluster_statuses",
    )


def test_spike_compiled_cluster_ir_matches_hand_written_combinators() -> None:
    assert _canonical_ir(cluster_slice.BATCH.to_ir()) == _canonical_ir(
        _hand_written_spike_cluster_ir()
    )


def test_spike_cluster_slice_dry_run_tallies_success_and_stale_snapshot() -> None:
    cluster_slice.reset_store()
    deployment = deploy(
        cluster_slice.BATCH.to_ir(),
        tools=cluster_slice.TOOLS,
        brains=[cluster_slice.LABEL_BRAIN, cluster_slice.KEYWORDS_BRAIN],
    )

    result = deployment.dry_run(
        cluster_slice.CLUSTERS,
        brains={
            cluster_slice.LABEL_BRAIN: cluster_slice._fake_labeler,
            cluster_slice.KEYWORDS_BRAIN: cluster_slice._fake_keywords,
        },
    )

    assert result.value["counts"] == {"success": 1, "stale_snapshot": 1}
    assert cluster_slice.store_labels() == {
        "cluster-10": {
            "keywords": ["Ada", "Ben"],
            "label": "Memory cluster 10",
            "summary": "Ada, Ben",
        }
    }


def test_partially_applied_flow_can_only_leave_one_each_item_parameter() -> None:
    with pytest.raises(ValueError, match="exactly one unbound item parameter"):

        @flow
        def three_arg_body(store_context, label_source, cluster):  # type: ignore[no-untyped-def]
            return think(cluster_slice.LABEL_BRAIN, label_source)

        each(three_arg_body({"storeId": "store-a"}))


def test_unsaturated_flow_application_as_runtime_value_is_actionable() -> None:
    with pytest.raises(TypeError, match="unsaturated @flow application"):

        @flow
        def returns_partial(source):  # type: ignore[no-untyped-def]
            return cluster_slice.label_one(source)


def test_rebinding_collision_is_caught_at_define_time() -> None:
    with pytest.raises(ValueError, match="already bound"):

        @flow
        def rebinds_source(source):  # type: ignore[no-untyped-def]
            source = think(cluster_slice.LABEL_BRAIN, source)
            return source
