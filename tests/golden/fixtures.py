"""Golden-corpus fixture builders for the spec's required §13 shapes."""

from __future__ import annotations

from dataclasses import dataclass

from composable_agents import (
    CapabilityManifest,
    Contract,
    Effect,
    Idempotency,
    app,
    call,
    deploy,
    each,
    hedge,
    human_gate,
    mcp,
    quorum,
    race,
    seq,
    stage,
    sub,
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
        flow=seq(call(mcp("srv", "extract")), call(mcp("srv", "summarize"))),
        snapshot=_read_snapshot("extract", "summarize"),
    )


def subagent_firewall() -> GoldenFixture:
    return GoldenFixture(
        name="subagent_firewall",
        flow=seq(
            call(mcp("srv", "parent_read")),
            sub("child.agent", Contract.agent()),
            call(mcp("srv", "parent_summarize")),
        ),
        snapshot=_read_snapshot("parent_read", "parent_summarize"),
    )


def each_fanout() -> GoldenFixture:
    return GoldenFixture(
        name="each_fanout",
        flow=seq(
            call(mcp("srv", "list_items")),
            each(call(mcp("srv", "process_item")), max_parallel=4),
        ),
        snapshot=_read_snapshot("list_items", "process_item"),
    )


def race_fixture() -> GoldenFixture:
    return GoldenFixture(
        name="race",
        flow=race(call(mcp("srv", "primary")), call(mcp("srv", "replica"))),
        snapshot=_read_snapshot("primary", "replica"),
        capabilities=_caps("primary", "replica"),
    )


def quorum_fixture() -> GoldenFixture:
    return GoldenFixture(
        name="quorum",
        flow=quorum(
            call(mcp("srv", "vote_a")),
            call(mcp("srv", "vote_b")),
            call(mcp("srv", "vote_c")),
            k=2,
        ),
        snapshot=_read_snapshot("vote_a", "vote_b", "vote_c"),
        capabilities=_caps("vote_a", "vote_b", "vote_c"),
    )


def hedge_fixture() -> GoldenFixture:
    return GoldenFixture(
        name="hedge",
        flow=hedge(call(mcp("srv", "near")), call(mcp("srv", "far")), hedge_ms=50),
        snapshot=_read_snapshot("near", "far"),
        capabilities=_caps("near", "far"),
    )


def human_gate_fixture() -> GoldenFixture:
    return GoldenFixture(
        name="human_gate",
        flow=seq(human_gate(timeout_s=60), call(mcp("srv", "record_approval"))),
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
        flow=app("support.controller"),
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
        flow=seq(call("native_index"), call(mcp("srv", "lookup"))),
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
            "brains": [],
            "memory": [],
            "budget": {"cost": 100.0, "tokens": 10000},
        }
    )
    return GoldenFixture(
        name="capability_manifest",
        flow=seq(call(mcp("srv", "search")), call(mcp("srv", "archive"))),
        snapshot=_read_snapshot("search", "archive"),
        capabilities=caps,
    )


FIXTURE_BUILDERS = {
    "simple_pipeline": simple_pipeline,
    "subagent_firewall": subagent_firewall,
    "each_fanout": each_fanout,
    "race": race_fixture,
    "quorum": quorum_fixture,
    "hedge": hedge_fixture,
    "human_gate": human_gate_fixture,
    "staged_plan": staged_plan,
    "agent_app": agent_app,
    "frozen_manifest": frozen_manifest,
    "capability_manifest": capability_manifest,
}
