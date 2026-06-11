from __future__ import annotations

import importlib
import sys

import pytest

import composable_agents.typed as _typed
from composable_agents import deploy
from composable_agents import dsl
from composable_agents.ir import Node, canonical_json
from composable_agents.transforms import normalize_ids
from examples import episode_summary_flow as episode

# spikes/ is frozen reference code that still imports the pre-rename typed
# module path; alias it to composable_agents.typed for these tests only.
sys.modules.setdefault("composable_agents." + "flow", _typed)

episode_slice = importlib.import_module("spikes.flow_spike.episode_slice")
_spike_core = importlib.import_module("spikes.flow_spike.core")
Handle = _spike_core.Handle
apply = _spike_core.apply
flow = _spike_core.flow
think = _spike_core.think


def _canonical_ir(node: Node) -> str:
    return canonical_json(normalize_ids(Node.from_json(node.to_json())).to_json())


def _hand_written_spike_episode_ir() -> Node:
    happy_path = dsl.seq(
        dsl.arr("spike.assign_source"),
        dsl.par(
            dsl.ident(),
            dsl.seq(dsl.arr("spike.pluck_source"), dsl.think(episode.SUMMARIZER)),
        ),
        dsl.arr("spike.assign_summary"),
        dsl.arr("spike.merge_source_summary"),
        dsl.arr("spike.assign_merged"),
        dsl.par(
            dsl.ident(),
            dsl.seq(dsl.arr("spike.pluck_merged"), dsl.think(episode.ONE_LINER)),
        ),
        dsl.arr("spike.assign_liner"),
        dsl.arr("spike.merge_merged_liner"),
        dsl.arr("spike.assign_return_arg"),
        dsl.par(
            dsl.ident(),
            dsl.seq(dsl.arr("spike.pluck_return_arg"), episode.write_summary_surfaces.to_ir()),
        ),
        dsl.arr("spike.assign_return_value"),
        dsl.arr("spike.pluck_return_value"),
    )

    summarize_one = dsl.seq(
        dsl.arr("spike.assign_episode_id"),
        dsl.par(
            dsl.ident(),
            dsl.seq(dsl.arr("spike.pluck_episode_id"), episode.read_episode.to_ir()),
        ),
        dsl.arr("spike.assign_source"),
        dsl.arr("spike.pluck_source"),
        dsl.alt(
            "episode_found",
            if_true=happy_path,
            if_false=dsl.arr("not_found_status"),
        ),
    )
    return dsl.each(summarize_one, max_parallel=2, reducer="tally_summary_statuses")


def test_spike_compiled_episode_ir_matches_hand_written_combinators() -> None:
    assert _canonical_ir(episode_slice.BATCH.to_ir()) == _canonical_ir(
        _hand_written_spike_episode_ir()
    )


def test_spike_episode_slice_dry_run_rolls_up_cas_statuses() -> None:
    episode.reset_store()
    deployment = deploy(
        episode_slice.BATCH.to_ir(),
        tools=episode.TOOLS,
        brains=[episode.SUMMARIZER, episode.ONE_LINER],
    )

    result = deployment.dry_run(
        episode.EPISODE_BATCH,
        brains={
            episode.SUMMARIZER: episode._fake_summarizer,
            episode.ONE_LINER: episode._fake_one_liner,
        },
    )

    assert result.value["counts"] == {"success": 2, "stale_source": 1, "not_found": 1}


def test_handle_truthiness_points_to_cond() -> None:
    with pytest.raises(TypeError, match=r"Use cond\("):
        bool(Handle.synthetic("source"))


def test_unregistered_plain_function_on_handle_is_actionable() -> None:
    def plain(value: object) -> object:
        return value

    with pytest.raises(TypeError, match="registered Tool, Pure, @flow function, or think"):
        apply(plain, Handle.synthetic("source"))


def test_missing_label_glue_is_actionable_at_define_time() -> None:
    with pytest.raises(ValueError, match=r"spike\.assign_missing"):

        @flow
        def needs_unregistered_label(source):  # type: ignore[no-untyped-def]
            missing = think("ad_hoc_brain", source)
            return missing
