from __future__ import annotations

from composable_agents.execution.interpreter import _unwrap_ca_meta


def test_unwrap_ca_meta_extracts_reply_and_attrs() -> None:
    assert _unwrap_ca_meta(
        {"__ca_meta__": {"tier": "BATCH", "batch_id": "b1"}, "reply": {"x": 1}}
    ) == ({"x": 1}, {"tier": "BATCH", "batch_id": "b1"})


def test_unwrap_ca_meta_leaves_plain_dict_untouched() -> None:
    assert _unwrap_ca_meta({"x": 1}) == ({"x": 1}, None)


def test_unwrap_ca_meta_preserves_summary_envelope() -> None:
    summary = {"__ca_summary__": "s", "reply": "r"}

    assert _unwrap_ca_meta(summary) == (summary, None)
