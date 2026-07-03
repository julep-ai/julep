from __future__ import annotations

import asyncio
from typing import Any

from composable_agents.agent_loop import AgentConfig, AgentState
from composable_agents.ir import ContextPolicy
from composable_agents.kinds import ContextScope, EnforcementMode
from composable_agents.transcript import SUMMARY_KEY
from composable_agents.turn import Halt, controller_turn, drive, pre_round


def _step(
    cfg: AgentConfig,
    replies: list[Any],
    calls: list[tuple[str, Any, int | None]] | None = None,
):
    async def invoke_controller(_payload: dict[str, Any]) -> Any:
        return replies.pop(0)

    async def call_tool(
        tool: str,
        value: Any,
        *,
        call_index: int | None = None,
    ) -> Any:
        if calls is None:
            raise AssertionError("call_tool ran unexpectedly")
        calls.append((tool, value, call_index))
        return {"tool": tool, "value": value, "index": call_index}

    return controller_turn(
        cfg=cfg,
        invoke_controller=invoke_controller,
        call_tool=call_tool,
        run_subflow=None,
        granted=None,
        granted_subflows=None,
        contracts=None,
        mode=EnforcementMode.STRICT,
        prod_gap=[],
        run_input={"task": "go"},
    )


def test_controller_turn_unwraps_llm_reply_meta_for_finish() -> None:
    cfg = AgentConfig()
    step = _step(
        cfg,
        [{"__ca_meta__": {"llm.model": "x"}, "reply": {"output": "done!"}}],
    )

    out = asyncio.run(drive(step, AgentState(last={"q": "x"}), halt=pre_round(cfg)))

    assert out["status"] == "done"
    assert out["output"] == "done!"


def test_controller_turn_unwraps_llm_reply_meta_for_native_tool_calls() -> None:
    calls: list[tuple[str, Any, int | None]] = []
    step = _step(
        AgentConfig(native_tools=True),
        [
            {
                "__ca_meta__": {"llm.model": "x"},
                "reply": {
                    "tool_calls": [
                        {"id": "a", "tool": "t", "input": {"n": 1}},
                    ],
                },
            }
        ],
        calls,
    )
    state = AgentState(last={"q": "x"})

    out = asyncio.run(step(state))

    assert out is state
    assert calls == [("t", {"n": 1}, 0)]
    assert state.last == [
        {
            "id": "a",
            "tool": "t",
            "output": {"tool": "t", "value": {"n": 1}, "index": 0},
        }
    ]
    assert [entry.to_json() for entry in state.trace] == [
        {"decision": "call", "cost": 1.0, "ref": "t", "callId": "a"}
    ]


def test_controller_turn_splits_summary_before_unwrapping_reply_meta() -> None:
    cfg = AgentConfig(
        ctx=ContextPolicy(scope=ContextScope.SUMMARY, max_tokens=100),
        summarizer="sum.reasoner",
    )
    step = _step(
        cfg,
        [
            {
                SUMMARY_KEY: "s",
                "__ca_meta__": {"llm.model": "x"},
                "reply": {"output": "done!"},
            }
        ],
    )
    state = AgentState(last={"q": "x"})

    out = asyncio.run(step(state))

    assert isinstance(out, Halt)
    assert out.status == "done"
    assert out.output == "done!"
    assert state.summary == "s"
