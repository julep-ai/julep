from __future__ import annotations

import asyncio
from typing import Any

import pytest

from julep import (
    CapabilityManifest,
    alt,
    arr,
    deploy,
    each,
    ident,
    par,
    pure,
    seq,
    snapshot_from_tools,
    think,
)
from examples import episode_summary_flow as episode


@pure("attach_summary")
def attach_summary(parts: list[dict[str, Any]]) -> dict[str, Any]:
    source, reply = parts
    return {**source, "summary": str(reply["summary"]).strip()}


@pure("attach_one_liner")
def attach_one_liner(parts: list[dict[str, Any]]) -> dict[str, Any]:
    merged, reply = parts
    return {**merged, "oneLiner": str(reply["oneLiner"]).strip()}


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


def _episode_capabilities(*, include_reasoners: bool = True) -> CapabilityManifest:
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
    if include_reasoners:
        data["reasoners"] = [episode.SUMMARIZER, episode.ONE_LINER]
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
        reasoners=[episode.SUMMARIZER, episode.ONE_LINER],
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


def test_deploy_rejects_reasoners_without_tools() -> None:
    with pytest.raises(ValueError, match="reasoners=.*tools="):
        deploy(
            _episode_batch(),
            snapshot_from_tools(episode.TOOLS),
            reasoners=[episode.SUMMARIZER],
        )


def test_deploy_rejects_reasoners_with_explicit_capabilities() -> None:
    explicit = _episode_capabilities(include_reasoners=False)

    with pytest.raises(ValueError, match="capabilities.*reasoners"):
        deploy(
            _episode_batch(),
            tools=episode.TOOLS,
            reasoners=["not-the-derived-reasoner-set"],
            capabilities=explicit,
        )


def test_deployment_refresh_retains_tools_for_dry_run() -> None:
    episode.reset_store()
    deployment = deploy(
        _episode_batch(),
        tools=episode.TOOLS,
        reasoners=[episode.SUMMARIZER, episode.ONE_LINER],
    )

    refreshed = deployment.refresh(snapshot_from_tools(episode.TOOLS))

    assert list(refreshed._tools or []) == episode.TOOLS
    assert "_tools" not in refreshed.artifact_components
    result = refreshed.dry_run(
        episode.EPISODE_BATCH,
        reasoners={
            episode.SUMMARIZER: episode._fake_summarizer,
            episode.ONE_LINER: episode._fake_one_liner,
        },
    )
    assert result.value["counts"]["success"] == 2


def test_deploy_accepts_flow_like_to_ir() -> None:
    class FlowWrapper:
        def to_ir(self):
            return episode.read_episode.to_ir()

    deployment = deploy(FlowWrapper(), tools=episode.TOOLS)

    assert deployment.flow_json["op"] == "prim"
    assert list(deployment._tools or []) == episode.TOOLS


def test_deployment_dry_run_reproduces_episode_demo_rollup() -> None:
    episode.reset_store()
    deployment = deploy(
        _episode_batch(),
        tools=episode.TOOLS,
        reasoners=[episode.SUMMARIZER, episode.ONE_LINER],
    )

    result = deployment.dry_run(
        episode.EPISODE_BATCH,
        reasoners={
            episode.SUMMARIZER: episode._fake_summarizer,
            episode.ONE_LINER: episode._fake_one_liner,
        },
    )

    assert result.value["counts"] == {
        "success": 2,
        "stale_source": 1,
        "not_found": 1,
    }


def test_deployment_dry_run_requires_deploy_tools_path() -> None:
    deployment = deploy(
        _episode_batch(),
        snapshot_from_tools(episode.TOOLS),
        capabilities=_episode_capabilities(),
    )

    with pytest.raises(ValueError, match=r"deploy\(tools=\.\.\.\)"):
        deployment.dry_run(episode.EPISODE_BATCH)


def test_deployment_adry_run_requires_deploy_tools_path() -> None:
    deployment = deploy(
        _episode_batch(),
        snapshot_from_tools(episode.TOOLS),
        capabilities=_episode_capabilities(),
    )

    async def run() -> None:
        with pytest.raises(ValueError, match=r"deploy\(tools=\.\.\.\)"):
            await deployment.adry_run(episode.EPISODE_BATCH)

    asyncio.run(run())
