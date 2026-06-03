from __future__ import annotations

from composable_agents import Budget, app
from composable_agents.ir import Node


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
        budget=Budget(usd=1),
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
        "budget": {"usd": 1},
        "maxRounds": 5,
    }
    assert back.to_json() == encoded
    assert back.tools == ["search", "archive"]
    assert back.subflows == ["child"]
    assert back.budget is not None
    assert back.budget.usd == 1
    assert back.max_rounds == 5
