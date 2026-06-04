from __future__ import annotations

import pytest

from composable_agents.dotctx import Brain, get_brain, register_brain
from composable_agents.dsl import alt, arr
from composable_agents.execution.interpreter import InMemoryEnv, interpret
from composable_agents.projection import InMemoryProjection, ProjectionEmitter
from composable_agents.purity import get_pure, pure
from composable_agents.registry import DEFAULT_REGISTRY, Registry
from conftest import run


def _iso_map(value):
    return {"iso": value}


def _default_map(value):
    return {"default": value}


def _iso_route(value):
    return "iso" if value["route"] else "fallback"


def _iso_project(value):
    return {"resolved": "iso", "value": value["value"]}


def test_registry_instances_are_isolated_from_each_other_and_default():
    left = Registry()
    right = Registry()
    brain = Brain(name="p2_2.iso.brain", model="model-left")

    assert left.register_brain(brain) is brain
    entry = left.register_pure("p2_2.iso.map", _iso_map)

    assert left.get_brain("p2_2.iso.brain") == brain
    assert left.get_pure("p2_2.iso.map")({"x": 1}) == {"iso": {"x": 1}}
    assert left.source_hash_of("p2_2.iso.map") == entry.source_hash

    with pytest.raises(KeyError):
        right.get_brain("p2_2.iso.brain")
    with pytest.raises(KeyError):
        DEFAULT_REGISTRY.get_brain("p2_2.iso.brain")
    assert not right.is_registered("p2_2.iso.map")
    assert not DEFAULT_REGISTRY.is_registered("p2_2.iso.map")
    with pytest.raises(KeyError):
        right.get_pure("p2_2.iso.map")
    with pytest.raises(KeyError):
        DEFAULT_REGISTRY.get_pure("p2_2.iso.map")


def test_default_registry_shims_preserve_existing_decorator_ergonomics():
    brain = Brain(name="p2_2.default.brain", model="model-default")

    assert register_brain(brain) is brain
    assert get_brain("p2_2.default.brain") == brain

    @pure("p2_2.default.map")
    def map_default(value):
        return _default_map(value)

    assert get_pure("p2_2.default.map")("x") == {"default": "x"}
    assert map_default("y") == {"default": "y"}


def test_in_memory_env_resolves_pures_from_injected_registry_not_global():
    iso = Registry()
    iso.register_pure("p2_2.env.route", _iso_route)
    iso.register_pure("p2_2.env.project", _iso_project)

    assert not DEFAULT_REGISTRY.is_registered("p2_2.env.route")
    with pytest.raises(KeyError):
        get_pure("p2_2.env.route")

    flow = alt(
        select="p2_2.env.route",
        cases={"iso": arr("p2_2.env.project")},
    )
    store = InMemoryProjection()
    env = InMemoryEnv({}, ProjectionEmitter(store), registry=iso)

    out = run(interpret(flow, {"route": True, "value": 7}, env))

    assert out.value == {"resolved": "iso", "value": 7}
