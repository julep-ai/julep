from __future__ import annotations

import pytest

from composable_agents.agent import Agent, tool
from composable_agents.dsl import call, native
from composable_agents.typed import as_flow
from composable_agents.flow_registry import FlowRegistryError, get_flow


def test_named_resolves_from_default_flow_registry() -> None:
    f = as_flow(call(native("tf5_named_x"))).named("tf5.svc.search.v1")

    assert f.name == "tf5.svc.search.v1"
    assert get_flow("tf5.svc.search.v1").node.to_json() == f.to_ir().to_json()


def test_named_does_not_change_emitted_ir() -> None:
    node = call(native("tf5_ir_x"))

    assert as_flow(node).named("tf5.r1").to_ir().to_json() == as_flow(node).to_ir().to_json()


def test_structural_composition_drops_flow_name() -> None:
    f = as_flow(call(native("tf5_affine_x"))).named("tf5.affine.seq")

    assert (f >> as_flow(call(native("tf5_affine_y")))).name is None


def test_agent_with_tools_and_without_drop_explicit_name() -> None:
    @tool(effect="read", idempotent=True, name="tf5_agent_t1")
    def t1(value: str) -> str:
        return value

    @tool(effect="read", idempotent=True, name="tf5_agent_t2")
    def t2(value: str) -> str:
        return value

    base = Agent("m", tools=[t1], name="tf5_base_explicit")
    with_added = base.with_tools(add=[t2])
    plain_added = Agent("m", tools=[t1, t2])
    without_t1 = base.without(t1)
    plain_without = Agent("m", tools=[])

    assert with_added._name != "tf5_base_explicit"
    assert with_added._name == plain_added._name
    assert without_t1._name != "tf5_base_explicit"
    assert without_t1._name == plain_without._name


def test_renamed_reasserts_and_can_replace_changed_flow() -> None:
    first = as_flow(call(native("tf5_rename_x"))) >> as_flow(call(native("tf5_rename_y")))
    second = as_flow(call(native("tf5_rename_x"))) >> as_flow(call(native("tf5_rename_z")))

    g = first.renamed("tf5.r2")
    replaced = second.renamed("tf5.r2")

    assert g.name == "tf5.r2"
    assert replaced.name == "tf5.r2"
    assert get_flow("tf5.r2").node.to_json() == replaced.to_ir().to_json()


def test_named_rejects_brain_name_collision() -> None:
    @tool(effect="read", idempotent=True, name="tf5_lookup_brain")
    def lookup_brain(value: str) -> str:
        return value

    Agent("m", tools=[lookup_brain], name="tf5_collide_brain_1")

    with pytest.raises(FlowRegistryError, match="collides"):
        as_flow(call(native("tf5_collision_z"))).named("tf5_collide_brain_1")


def test_named_rejects_registered_agent_tool_name_collision() -> None:
    @tool(effect="read", idempotent=True, name="tf5_lookup_tool")
    def lookup_tool(value: str) -> str:
        return value

    Agent("m", tools=[lookup_tool], name="tf5_collide_tool_agent")

    with pytest.raises(FlowRegistryError, match="collides"):
        as_flow(call(native("tf5_collision_tool_z"))).named("tf5_lookup_tool")


def test_derived_local_name_is_deterministic_for_structurally_equal_flows() -> None:
    a1 = call(native("tf5_local_name_x"))
    a2 = call(native("tf5_local_name_x"))

    assert as_flow(a1).local_name == as_flow(a2).local_name
    assert as_flow(a1).local_name.startswith("flow-")


def test_named_is_idempotent_for_fresh_structurally_equal_flows() -> None:
    as_flow(call(native("c1_x"))).named("c1.svc")

    as_flow(call(native("c1_x"))).named("c1.svc")

    assert get_flow("c1.svc").ref == "c1.svc"

    with pytest.raises(FlowRegistryError, match="different flow"):
        as_flow(call(native("c1_y"))).named("c1.svc")
