"""Golden-corpus fixture builders for the spec's required §13 shapes."""

from __future__ import annotations

from dataclasses import dataclass

from composable_agents import (
    CapabilityManifest,
    Contract,
    Effect,
    Idempotency,
    call,
    deploy,
    escalate,
    hedge,
    human_gate,
    mcp_call,
    pipeline,
    quorum,
    race,
    stage,
    subagent,
)
from composable_agents.contracts import ToolContract
from composable_agents.deploy import Deployment, snapshot_from_listings
from composable_agents.freeze import McpSnapshot, NativeToolSpec
from composable_agents.ir import Node


@dataclass(frozen=True)
class GoldenFixture:
    """A buildable deployment fixture, or a documented skip."""

    name: str
    flow: Node
    snapshot: McpSnapshot
    capabilities: CapabilityManifest | None = None
    skip_reason: str | None = None

    def deploy(self) -> Deployment:
        return deploy(
            self.flow,
            self.snapshot,
            capabilities=self.capabilities,
            strict=False,
        )


def _read_snapshot(*tool_names: str) -> McpSnapshot:
    return snapshot_from_listings(
        {
            "srv": {
                name: {
                    "inputSchema": {"type": "object"},
                    "annotations": {"readOnlyHint": True, "idempotentHint": True},
                }
                for name in tool_names
            }
        }
    )


def _caps(*tool_names: str) -> CapabilityManifest:
    return CapabilityManifest.from_dict(
        {
            "tools": [
                {"name": f"srv/{name}", "effect": "read", "idempotency": "native"}
                for name in tool_names
            ],
            "mcp_servers": {"srv": None},
        }
    )


def simple_pipeline() -> GoldenFixture:
    return GoldenFixture(
        name="simple_pipeline",
        flow=pipeline(mcp_call("srv", "extract"), mcp_call("srv", "summarize")),
        snapshot=_read_snapshot("extract", "summarize"),
    )


def subagent_firewall() -> GoldenFixture:
    return GoldenFixture(
        name="subagent_firewall",
        flow=pipeline(
            mcp_call("srv", "parent_read"),
            subagent("child.agent", Contract.agent()),
            mcp_call("srv", "parent_summarize"),
        ),
        snapshot=_read_snapshot("parent_read", "parent_summarize"),
    )


def race_fixture() -> GoldenFixture:
    return GoldenFixture(
        name="race",
        flow=race(mcp_call("srv", "primary"), mcp_call("srv", "replica")),
        snapshot=_read_snapshot("primary", "replica"),
        capabilities=_caps("primary", "replica"),
    )


def quorum_fixture() -> GoldenFixture:
    return GoldenFixture(
        name="quorum",
        flow=quorum(
            mcp_call("srv", "vote_a"),
            mcp_call("srv", "vote_b"),
            mcp_call("srv", "vote_c"),
            m=2,
        ),
        snapshot=_read_snapshot("vote_a", "vote_b", "vote_c"),
        capabilities=_caps("vote_a", "vote_b", "vote_c"),
    )


def hedge_fixture() -> GoldenFixture:
    return GoldenFixture(
        name="hedge",
        flow=hedge(mcp_call("srv", "near"), mcp_call("srv", "far"), after_ms=50),
        snapshot=_read_snapshot("near", "far"),
        capabilities=_caps("near", "far"),
    )


def human_gate_fixture() -> GoldenFixture:
    return GoldenFixture(
        name="human_gate",
        flow=pipeline(human_gate(timeout_s=60), mcp_call("srv", "record_approval")),
        snapshot=_read_snapshot("record_approval"),
    )


def staged_plan() -> GoldenFixture:
    return GoldenFixture(
        name="staged_plan",
        flow=stage("planner.brain"),
        snapshot=McpSnapshot(),
    )


def agent_app() -> GoldenFixture:
    return GoldenFixture(
        name="agent_app",
        flow=escalate("support.controller"),
        snapshot=McpSnapshot(),
    )


def frozen_manifest() -> GoldenFixture:
    base = _read_snapshot("lookup")
    snapshot = McpSnapshot(
        servers=base.servers,
        native={
            "native_index": NativeToolSpec(
                input_schema={"type": "object"},
                contract=ToolContract(Effect.READ, Idempotency.NATIVE),
                output_schema={"type": "object"},
            )
        },
    )
    return GoldenFixture(
        name="frozen_manifest",
        flow=pipeline(call("native_index"), mcp_call("srv", "lookup")),
        snapshot=snapshot,
    )


def capability_manifest() -> GoldenFixture:
    caps = CapabilityManifest.from_dict(
        {
            "tools": [
                {"name": "srv/search", "effect": "read", "idempotency": "native"},
                {"name": "srv/archive", "effect": "write", "idempotency": "required"},
            ],
            "mcp_servers": {"srv": None},
            "models": [],
            "memory": [],
            "budget": {"usd": 100.0, "tokens": 10000},
        }
    )
    return GoldenFixture(
        name="capability_manifest",
        flow=pipeline(mcp_call("srv", "search"), mcp_call("srv", "archive")),
        snapshot=_read_snapshot("search", "archive"),
        capabilities=caps,
    )


FIXTURE_BUILDERS = {
    "simple_pipeline": simple_pipeline,
    "subagent_firewall": subagent_firewall,
    "race": race_fixture,
    "quorum": quorum_fixture,
    "hedge": hedge_fixture,
    "human_gate": human_gate_fixture,
    "staged_plan": staged_plan,
    "agent_app": agent_app,
    "frozen_manifest": frozen_manifest,
    "capability_manifest": capability_manifest,
}
