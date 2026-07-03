"""Red-phase coverage for native tool-call transcript round-trips."""

from __future__ import annotations

import json

from composable_agents.agent_loop import AgentState, TraceEntry
from composable_agents.execution.llm import _transcript_messages
from composable_agents.ir import ContextPolicy
from composable_agents.kinds import ContextScope
from composable_agents.transcript import Turn, split_to_budget, transcript_for

WHOLE = ContextPolicy(scope=ContextScope.WHOLE_SESSION, max_tokens=1000)


def test_native_call_entry_projects_tool_call_turns() -> None:
    state = AgentState(
        trace=[
            TraceEntry(
                decision="call",
                ref="search",
                call_id="call_1",
                input_ref="t/sha256:" + "a" * 64,
                output_ref="t/sha256:" + "b" * 64,
            )
        ],
    )

    plan = transcript_for(state, WHOLE, input={"task": "go"})

    assert plan[1]["tool_call_id"] == "call_1"
    assert plan[1]["tool_calls"] == [
        {
            "id": "call_1",
            "type": "function",
            "function": {"name": "search", "arguments": ""},
        }
    ]
    assert plan[2]["tool_call_id"] == "call_1"


def test_idless_entries_project_exactly_as_before() -> None:
    state = AgentState(
        trace=[
            TraceEntry(
                decision="call",
                ref="search",
                input_ref="t/sha256:" + "a" * 64,
                output_ref="t/sha256:" + "b" * 64,
            )
        ],
    )

    plan = transcript_for(state, WHOLE, input={"task": "go"})

    expected = [
        {"role": "user", "content": {"task": "go"}},
        {
            "role": "assistant",
            "ref": {"kind": "native", "name": "search"},
            "content_ref": "t/sha256:" + "a" * 64,
        },
        {
            "role": "tool",
            "ref": {"kind": "native", "name": "search"},
            "content_ref": "t/sha256:" + "b" * 64,
        },
    ]
    assert plan == expected
    assert "tool_call_id" not in plan[1]
    assert "tool_calls" not in plan[1]
    assert "tool_call_id" not in plan[2]
    assert "tool_calls" not in plan[2]


def test_transcript_messages_native_pair() -> None:
    tool_call = {
        "id": "call_1",
        "type": "function",
        "function": {"name": "search", "arguments": ""},
    }
    transcript = [
        {
            "role": "assistant",
            "content": {"q": "x"},
            "tool_calls": [tool_call],
        },
        {
            "role": "tool",
            "tool_call_id": "call_1",
            "content": {"hits": 2},
        },
    ]

    assert _transcript_messages(transcript) == [
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "search",
                        "arguments": json.dumps({"q": "x"}, sort_keys=True),
                    },
                }
            ],
        },
        {
            "role": "tool",
            "tool_call_id": "call_1",
            "content": json.dumps({"hits": 2}, sort_keys=True),
        },
    ]


def test_transcript_messages_arguments_default_when_no_content() -> None:
    transcript = [
        {
            "role": "assistant",
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "search", "arguments": ""},
                }
            ],
        }
    ]

    assert _transcript_messages(transcript) == [
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "search", "arguments": "{}"},
                }
            ],
        }
    ]


def test_transcript_messages_idless_golden() -> None:
    transcript = [
        {
            "role": "assistant",
            "ref": {"kind": "native", "name": "search"},
            "content": {"q": "x"},
        },
        {
            "role": "tool",
            "ref": {"kind": "native", "name": "search"},
            "content": {"hits": 2},
        },
        {"role": "system", "content": "prior context"},
        {"role": "user", "content": {"task": "continue"}},
    ]

    assert _transcript_messages(transcript) == [
        {
            "role": "assistant",
            "content": f"[called search] {json.dumps({'q': 'x'}, sort_keys=True)}",
        },
        {
            "role": "user",
            "content": f"[search result] {json.dumps({'hits': 2}, sort_keys=True)}",
        },
        {"role": "system", "content": "prior context"},
        {"role": "user", "content": json.dumps({"task": "continue"}, sort_keys=True)},
    ]


def test_mixed_transcript_ordering_preserved() -> None:
    native_call = {
        "id": "call_1",
        "type": "function",
        "function": {"name": "fetch", "arguments": ""},
    }
    transcript = [
        {
            "role": "assistant",
            "ref": {"kind": "native", "name": "search"},
            "content": None,
        },
        {
            "role": "tool",
            "ref": {"kind": "native", "name": "search"},
            "content": {"hits": 1},
        },
        {
            "role": "assistant",
            "content": {"url": "https://example.test"},
            "tool_calls": [native_call],
        },
        {
            "role": "tool",
            "tool_call_id": "call_1",
            "content": "ok",
        },
    ]

    assert _transcript_messages(transcript) == [
        {"role": "assistant", "content": "[called search]"},
        {
            "role": "user",
            "content": f"[search result] {json.dumps({'hits': 1}, sort_keys=True)}",
        },
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "fetch",
                        "arguments": json.dumps(
                            {"url": "https://example.test"},
                            sort_keys=True,
                        ),
                    },
                }
            ],
        },
        {"role": "tool", "tool_call_id": "call_1", "content": "ok"},
    ]


def test_split_to_budget_never_orphans_tool_results() -> None:
    user: Turn = {"role": "user", "content": "old"}
    assistant: Turn = {
        "role": "assistant",
        "content": {"q": "x"},
        "tool_call_id": "call_1",
        "tool_calls": [
            {
                "id": "call_1",
                "type": "function",
                "function": {"name": "search", "arguments": ""},
            }
        ],
    }
    tool: Turn = {
        "role": "tool",
        "tool_call_id": "call_1",
        "content": {"hits": 2},
    }
    plain: Turn = {"role": "assistant", "content": "newer reply"}
    turns = [user, assistant, tool, plain]

    elided, kept = split_to_budget(turns, 2, lambda text: 1)

    assert kept == [plain]
    assert elided == [user, assistant, tool]


def test_split_to_budget_idless_behavior_unchanged() -> None:
    user: Turn = {"role": "user", "content": "old"}
    assistant: Turn = {
        "role": "assistant",
        "ref": {"kind": "native", "name": "search"},
        "content": {"q": "x"},
    }
    tool: Turn = {
        "role": "tool",
        "ref": {"kind": "native", "name": "search"},
        "content": {"hits": 2},
    }
    plain: Turn = {"role": "assistant", "content": "newer reply"}
    turns = [user, assistant, tool, plain]

    elided, kept = split_to_budget(turns, 2, lambda text: 1)

    assert kept == [tool, plain]
    assert elided == [user, assistant]
