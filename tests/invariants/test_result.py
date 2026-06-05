from __future__ import annotations

import json
from typing import Any

from composable_agents import Agent, tool
from composable_agents.result import Result


def test_result_dual_attribute_and_dict_access() -> None:
    raw = {
        "status": "done",
        "output": {"note": "x"},
        "trace": [{"decision": "call"}],
        "cost": 1.5,
        "rounds": 2,
    }
    r = Result(raw)

    assert r.status == "done"
    assert r.ok is True
    assert r.output == {"note": "x"}
    assert r.trace == [{"decision": "call"}]
    assert r.cost == 1.5
    assert r.rounds == 2

    assert r["status"] == "done"
    assert r["output"]["note"] == "x"
    assert r["cost"] == 1.5
    assert r.get("rounds") == 2
    assert "status" in r
    assert "denied" not in r
    assert r == raw
    assert isinstance(r, dict)
    json.dumps(r)


def test_result_ok_reflects_status_and_reason() -> None:
    r = Result({"status": "denied", "reason": "tool not granted"})

    assert r.ok is False
    assert r.reason == "tool not granted"


def test_result_prod_gap_reads_optional_prod_gap() -> None:
    with_gap = Result({"prodGap": ["approval required"]})
    without_gap = Result({})

    assert with_gap.prod_gap == ["approval required"]
    assert without_gap.prod_gap is None


def test_agent_run_returns_result_and_remains_dict_compatible() -> None:
    @tool(effect="read", idempotent=True)
    def a_read_tool(value: str) -> str:
        return f"read:{value}"

    def llm(_brain_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        return {"output": {"echo": payload["input"]}}

    result = Agent("m", tools=[a_read_tool], name="tf8_agent", llm=llm).run("hi")

    assert isinstance(result, Result)
    assert isinstance(result, dict)
    assert result.status == "done"
    assert result["status"] == "done"
    assert result.ok is True
    assert result.output == result["output"]
