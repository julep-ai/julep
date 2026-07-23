from __future__ import annotations

import asyncio

import pytest

from julep import (
    CapabilityManifest,
    deploy,
    snapshot_from_listings,
    snapshot_from_tools,
    tool,
)
from examples import episode_summary_flow as episode


@tool(effect="read", idempotent=True)
def ws2_native_echo(value: dict[str, object]) -> dict[str, object]:
    return dict(value)


def _snapshot():
    return snapshot_from_listings(episode.mcp_listings())


def _episode_capabilities(*, include_reasoners: bool = True) -> CapabilityManifest:
    data: dict[str, object] = {
        "tools": [
            {
                "name": f"{episode.MCP_SERVER}/read_episode",
                "effect": "read",
                "idempotency": "native",
            },
            {
                "name": f"{episode.MCP_SERVER}/write_summary_surfaces",
                "effect": "write",
                "idempotency": "native",
            },
        ],
    }
    if include_reasoners:
        data["reasoners"] = [episode.SUMMARIZER, episode.ONE_LINER]
    return CapabilityManifest.from_dict(data)


def _native_capabilities() -> CapabilityManifest:
    return CapabilityManifest.from_dict(
        {
            "tools": [
                {
                    "name": ws2_native_echo.name,
                    "effect": "read",
                    "idempotency": "native",
                }
            ]
        }
    )


def test_native_tools_path_still_derives_capabilities_and_retains_runtime_tools() -> None:
    snapshot = snapshot_from_tools([ws2_native_echo])
    oracle = deploy(ws2_native_echo, snapshot, capabilities=_native_capabilities())
    derived = deploy(ws2_native_echo, tools=[ws2_native_echo])

    assert derived.artifact_hash == oracle.artifact_hash
    assert derived.capabilities is not None
    assert derived.capabilities.to_json() == _native_capabilities().to_json()
    assert list(derived._tools or ()) == [ws2_native_echo]
    assert derived.dry_run({"value": 3}).value == {"value": 3}


def test_native_refresh_retains_tools_and_snapshot_only_dry_run_still_rejects() -> None:
    snapshot = snapshot_from_tools([ws2_native_echo])
    deployment = deploy(ws2_native_echo, tools=[ws2_native_echo])

    refreshed = deployment.refresh(snapshot)
    assert list(refreshed._tools or ()) == [ws2_native_echo]
    assert refreshed.dry_run({"value": 4}).value == {"value": 4}

    snapshot_only = deploy(
        ws2_native_echo,
        snapshot,
        capabilities=_native_capabilities(),
    )
    with pytest.raises(ValueError, match=r"deploy\(tools=\.\.\.\)"):
        snapshot_only.dry_run({"value": 5})


def test_deploy_mcp_listings_derives_capabilities_from_frozen_tools() -> None:
    deployment = deploy(
        episode.batch,
        mcp_listings=episode.mcp_listings(),
    )

    assert deployment.capabilities is not None
    assert deployment.capabilities.to_json() == _episode_capabilities().to_json()
    assert deployment._tools is None
    assert "_tools" not in deployment.artifact_components


def test_deploy_mcp_servers_fetches_with_the_configured_url_allowlist(monkeypatch) -> None:
    servers = {
        episode.MCP_SERVER: {
            "url": "https://episodes.example.test/mcp",
            "headers": {"X-Tenant": "demo"},
        }
    }
    received: list[tuple[object, object]] = []

    def snapshot_servers(configured, *, allowlist):
        received.append((configured, allowlist))
        return _snapshot()

    monkeypatch.setattr("julep.mcp_snapshot.snapshot_servers", snapshot_servers)

    deployment = deploy(episode.read_episode, mcp_servers=servers)

    assert received == [(servers, frozenset({"https://episodes.example.test/mcp"}))]
    assert deployment.capabilities is not None
    assert set(deployment.capabilities.tools) == {f"{episode.MCP_SERVER}/read_episode"}


def test_deploy_positional_mcp_snapshot_path_is_deterministic() -> None:
    snapshot = _snapshot()
    capabilities = _episode_capabilities()

    first = deploy(episode.batch, snapshot, capabilities=capabilities)
    second = deploy(episode.batch, snapshot, capabilities=capabilities)

    assert second.artifact_hash == first.artifact_hash
    assert first._tools is None
    assert second._tools is None


def test_deploy_explicit_snapshot_wins_over_lower_priority_sources(monkeypatch) -> None:
    explicit = _snapshot()

    def unexpected_live_fetch(*_args, **_kwargs):
        raise AssertionError("explicit snapshot must prevent live MCP fetches")

    monkeypatch.setattr("julep.mcp_snapshot.snapshot_servers", unexpected_live_fetch)

    expected = deploy(episode.batch, explicit)
    actual = deploy(
        episode.batch,
        explicit,
        mcp_listings={},
        mcp_servers={"ignored": {"url": "https://ignored.example/mcp"}},
        tools=[],
    )

    assert actual.artifact_hash == expected.artifact_hash
    assert actual._tools is None


def test_deploy_rejects_multiple_generated_sources_without_snapshot() -> None:
    with pytest.raises(ValueError, match="exactly one generated tool source"):
        deploy(episode.batch, mcp_listings=episode.mcp_listings(), tools=[])


def test_deploy_rejects_missing_tool_source() -> None:
    with pytest.raises(ValueError, match="snapshot.*tools"):
        deploy(episode.batch)


def test_deploy_derives_referenced_reasoners_with_explicit_mcp_snapshot() -> None:
    deployment = deploy(episode.batch, _snapshot())

    assert deployment.capabilities is not None
    assert deployment.capabilities.reasoners == {episode.SUMMARIZER, episode.ONE_LINER}


def test_deploy_rejects_reasoners_with_explicit_capabilities() -> None:
    explicit = _episode_capabilities(include_reasoners=False)

    with pytest.raises(ValueError, match="capabilities.*reasoners"):
        deploy(
            episode.batch,
            _snapshot(),
            reasoners=["not-the-derived-reasoner-set"],
            capabilities=explicit,
        )


def test_deployment_refresh_keeps_mcp_dry_run_path() -> None:
    episode.reset_store()
    deployment = episode.build()

    refreshed = deployment.refresh(_snapshot())

    assert refreshed._tools is None
    assert "_tools" not in refreshed.artifact_components
    result = refreshed.dry_run(
        episode.EPISODE_BATCH,
        mcp_call=episode._fake_mcp_call,
        reasoners={
            episode.SUMMARIZER: episode._fake_summarizer,
            episode.ONE_LINER: episode._fake_one_liner,
        },
    )
    assert result.value["counts"]["success"] == 2


def test_deploy_accepts_mcp_flow_like_to_ir() -> None:
    class FlowWrapper:
        def to_ir(self):
            return episode.read_episode.to_ir()

    deployment = deploy(FlowWrapper(), mcp_listings=episode.mcp_listings())

    assert deployment.flow_json["op"] == "prim"
    assert deployment._tools is None


def test_deployment_dry_run_reproduces_episode_demo_rollup() -> None:
    episode.reset_store()
    deployment = episode.build()

    result = deployment.dry_run(
        episode.EPISODE_BATCH,
        mcp_call=episode._fake_mcp_call,
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


def test_deployment_dry_run_requires_mcp_caller() -> None:
    deployment = episode.build()

    with pytest.raises(ValueError, match="mcp_call"):
        deployment.dry_run(episode.EPISODE_BATCH)


def test_deployment_adry_run_requires_mcp_caller() -> None:
    deployment = episode.build()

    async def run() -> None:
        with pytest.raises(ValueError, match="mcp_call"):
            await deployment.adry_run(episode.EPISODE_BATCH)

    asyncio.run(run())
