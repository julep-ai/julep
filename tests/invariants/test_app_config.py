from __future__ import annotations

import asyncio

from julep import Budget, app
from julep.execution.interpreter import InMemoryEnv, interpret
from julep.projection import InMemoryProjection, ProjectionEmitter
from julep.ir import Node


def test_bare_app_json_is_unchanged():
    flow = app("c")

    assert flow.to_json() == {
        "op": "app",
        "id": flow.id,
        "controller": "c",
    }


def test_app_inline_config_json_round_trips():
    flow = app(
        "c",
        tools=["search", "archive"],
        subflows=["child"],
        budget=Budget(cost=1),
        max_rounds=5,
    )

    encoded = flow.to_json()
    back = Node.from_json(encoded)

    assert encoded == {
        "op": "app",
        "id": flow.id,
        "controller": "c",
        "tools": ["search", "archive"],
        "subflows": ["child"],
        "budget": {"cost": 1},
        "maxRounds": 5,
    }
    assert back.to_json() == encoded
    assert back.tools == ["search", "archive"]
    assert back.subflows == ["child"]
    assert back.budget is not None
    assert back.budget.cost == 1
    assert back.max_rounds == 5


def test_app_inline_config_reaches_interpreter_env_run_agent() -> None:
    seen: dict[str, object] = {}

    class CapturingEnv(InMemoryEnv):
        async def run_agent(self, controller, value, cid, app_config=None):  # noqa: ANN001
            seen["controller"] = controller
            seen["value"] = value
            seen["app_config"] = app_config
            return "ok"

    store = InMemoryProjection()
    env = CapturingEnv({}, ProjectionEmitter(store))
    flow = app(
        "ctrl",
        tools=[],
        subflows=["child"],
        budget=Budget(cost=1),
        max_rounds=5,
    )

    out = asyncio.run(interpret(flow, {"q": "x"}, env))

    assert out.value == "ok"
    assert seen == {
        "controller": "ctrl",
        "value": {"q": "x"},
        "app_config": {
            "tools": [],
            "subflows": ["child"],
            "budget": {"cost": 1},
            "maxRounds": 5,
        },
    }
