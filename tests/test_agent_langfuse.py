from __future__ import annotations

import asyncio
from typing import Any

from composable_agents import Agent


def test_agent_calls_langfuse_export_hook() -> None:
    captured: dict[str, Any] = {}

    def hook(events: Any, run_id: str) -> None:
        captured["events"] = list(events)
        captured["run_id"] = run_id

    def llm(_reasoner_name: str, _payload: dict[str, Any]) -> dict[str, str]:
        return {"output": "final"}

    agent = Agent(
        "m",
        tools=[],
        name="agent_langfuse_export",
        llm=llm,
        langfuse_export=hook,
    )
    asyncio.run(agent.arun("hi"))

    assert captured["run_id"]
    assert any(event.type.name == "DID" for event in captured["events"])
