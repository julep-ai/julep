"""Golden-corpus fixture builders for the spec's required §13 shapes."""

from __future__ import annotations

from dataclasses import dataclass

from julep import (
    CapabilityManifest,
    Contract,
    Effect,
    Idempotency,
    app,
    call,
    cond,
    deploy,
    each,
    flow,
    hedge,
    human_gate,
    mcp,
    mcp_tool,
    pure,
    quorum,
    race,
    seq,
    stage,
    sub,
)
from julep.contracts import ToolContract
from julep.deploy import Deployment, snapshot_from_listings
from julep.freeze import McpSnapshot, NativeToolSpec
from julep.ir import Node


_record_lookup = mcp_tool("srv", "record_lookup")


@pure("golden.record.enabled")
def _record_enabled(value: dict[str, object]) -> bool:
    return bool(value.get("enabled"))


@flow
def _record_straight_flow(source: dict[str, object]) -> dict[str, object]:
    collection = source["collection"]
    query = source["query"]
    return _record_lookup(collection=collection, query=query, limit=10)


@flow
def _record_cond_arm(subject: dict[str, object]) -> dict[str, object]:
    collection = subject["collection"]
    query = subject["query"]
    return _record_lookup(collection=collection, query=query, branch="selected")


@flow
def _record_cond_flow(source: dict[str, object]) -> dict[str, object]:
    subject = source["subject"]
    return cond(
        _record_enabled,
        subject,
        then=_record_cond_arm,
        orelse=_record_cond_arm,
    )


@flow
def _record_each_body(item: dict[str, object]) -> dict[str, object]:
    item_id = item["id"]
    query = item["query"]
    return _record_lookup(item_id=item_id, query=query)


@flow
def _record_each_flow(source: dict[str, object]) -> list[dict[str, object]]:
    items = source["items"]
    return each(_record_each_body, items, max_parallel=2)


@flow
def _record_inline_child(source: dict[str, object]) -> dict[str, object]:
    collection = source["collection"]
    query = source["query"]
    return _record_lookup(collection=collection, query=query, inline=True)


@flow
def _record_inline_flow(source: dict[str, object]) -> dict[str, object]:
    return _record_inline_child(source)


@flow
def _record_rename_arm(
    source: dict[str, object],
    ctx: dict[str, object],
) -> dict[str, object]:
    source_id = source["id"]
    context_id = ctx["id"]
    return _record_lookup(source_id=source_id, context_id=context_id)


@flow
def _record_rename_child(source: dict[str, object]) -> dict[str, object]:
    ctx = source["child"]
    return cond(
        _record_enabled,
        source,
        then=_record_rename_arm(ctx=ctx),
        orelse=_record_rename_arm(ctx=ctx),
    )


@flow
def _record_external_rename_flow(source: dict[str, object]) -> dict[str, object]:
    ctx = source["parent"]
    child_result = _record_rename_child(source)
    parent_id = ctx["id"]
    return _record_lookup(child_result=child_result, parent_id=parent_id)


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
        flow=stage("planner.reasoner"),
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
            "reasoners": [],
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


def record_binding_straight() -> GoldenFixture:
    return GoldenFixture(
        name="record_binding_straight",
        flow=_record_straight_flow.to_ir(),
        snapshot=_read_snapshot("record_lookup"),
    )


def record_binding_cond() -> GoldenFixture:
    return GoldenFixture(
        name="record_binding_cond",
        flow=_record_cond_flow.to_ir(),
        snapshot=_read_snapshot("record_lookup"),
    )


def record_binding_each() -> GoldenFixture:
    return GoldenFixture(
        name="record_binding_each",
        flow=_record_each_flow.to_ir(),
        snapshot=_read_snapshot("record_lookup"),
    )


def record_binding_inline() -> GoldenFixture:
    return GoldenFixture(
        name="record_binding_inline",
        flow=_record_inline_flow.to_ir(),
        snapshot=_read_snapshot("record_lookup"),
    )


def record_binding_external_rename() -> GoldenFixture:
    return GoldenFixture(
        name="record_binding_external_rename",
        flow=_record_external_rename_flow.to_ir(),
        snapshot=_read_snapshot("record_lookup"),
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
    "record_binding_straight": record_binding_straight,
    "record_binding_cond": record_binding_cond,
    "record_binding_each": record_binding_each,
    "record_binding_inline": record_binding_inline,
    "record_binding_external_rename": record_binding_external_rename,
}
