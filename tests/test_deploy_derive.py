from __future__ import annotations

import pytest

from composable_agents import (
    CapabilityManifest,
    alt,
    arr,
    deploy,
    each,
    ident,
    par,
    seq,
    snapshot_from_tools,
    think,
)
from examples import episode_summary_flow as episode


def _episode_batch():
    summarize_one = seq(
        episode.read_episode.to_ir(),
        alt(
            "episode_found",
            if_true=seq(
                par(ident(), think(episode.SUMMARIZER)),
                arr("attach_summary"),
                par(ident(), think(episode.ONE_LINER)),
                arr("attach_one_liner"),
                episode.write_summary_surfaces.to_ir(),
            ),
            if_false=arr("not_found_status"),
        ),
    )
    return each(summarize_one, max_parallel=2, reducer="tally_summary_statuses")


def _episode_capabilities(*, include_brains: bool = True) -> CapabilityManifest:
    data: dict[str, object] = {
        "tools": [
            {
                "name": episode.read_episode.name,
                "effect": "read",
                "idempotency": "native",
            },
            {
                "name": episode.write_summary_surfaces.name,
                "effect": "write",
                "idempotency": "native",
            },
        ],
    }
    if include_brains:
        data["brains"] = [episode.SUMMARIZER, episode.ONE_LINER]
    return CapabilityManifest.from_dict(data)


def test_deploy_tools_path_matches_episode_capability_oracle_hash() -> None:
    batch = _episode_batch()
    oracle_capabilities = _episode_capabilities()

    old_path = deploy(
        batch,
        snapshot_from_tools(episode.TOOLS),
        capabilities=oracle_capabilities,
    )
    derived = deploy(
        batch,
        tools=episode.TOOLS,
        brains=[episode.SUMMARIZER, episode.ONE_LINER],
    )

    assert derived.artifact_hash == old_path.artifact_hash
    assert derived.capabilities is not None
    assert derived.capabilities.to_json() == oracle_capabilities.to_json()
    assert list(derived._tools or []) == episode.TOOLS
    assert "_tools" not in derived.artifact_components


def test_deploy_positional_snapshot_path_keeps_hash_and_no_tools() -> None:
    batch = _episode_batch()
    snapshot = snapshot_from_tools(episode.TOOLS)
    capabilities = _episode_capabilities()

    first = deploy(batch, snapshot, capabilities=capabilities)
    second = deploy(batch, snapshot, capabilities=capabilities)

    assert second.artifact_hash == first.artifact_hash
    assert first._tools is None
    assert second._tools is None


def test_deploy_rejects_snapshot_and_tools() -> None:
    with pytest.raises(ValueError, match="snapshot.*tools"):
        deploy(
            _episode_batch(),
            snapshot_from_tools(episode.TOOLS),
            tools=episode.TOOLS,
        )


def test_deploy_rejects_missing_snapshot_and_tools() -> None:
    with pytest.raises(ValueError, match="snapshot.*tools"):
        deploy(_episode_batch())


def test_deploy_rejects_brains_without_tools() -> None:
    with pytest.raises(ValueError, match="brains=.*tools="):
        deploy(
            _episode_batch(),
            snapshot_from_tools(episode.TOOLS),
            brains=[episode.SUMMARIZER],
        )


def test_deploy_tools_path_respects_explicit_capabilities() -> None:
    explicit = _episode_capabilities(include_brains=False)

    deployment = deploy(
        _episode_batch(),
        tools=episode.TOOLS,
        brains=["not-the-derived-brain-set"],
        capabilities=explicit,
    )

    assert deployment.capabilities is explicit
    assert "brains" not in deployment.capabilities.to_json()


def test_deploy_accepts_flow_like_to_ir() -> None:
    class FlowWrapper:
        def to_ir(self):
            return episode.read_episode.to_ir()

    deployment = deploy(FlowWrapper(), tools=episode.TOOLS)

    assert deployment.flow_json["op"] == "prim"
    assert list(deployment._tools or []) == episode.TOOLS
