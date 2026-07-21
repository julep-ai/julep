from __future__ import annotations

from julep.execution.interpreter import _unwrap_julep_meta


def test_unwrap_julep_meta_extracts_reply_and_attrs() -> None:
    assert _unwrap_julep_meta(
        {"__julep_meta__": {"tier": "BATCH", "batch_id": "b1"}, "reply": {"x": 1}}
    ) == ({"x": 1}, {"tier": "BATCH", "batch_id": "b1"})


def test_unwrap_julep_meta_leaves_plain_dict_untouched() -> None:
    assert _unwrap_julep_meta({"x": 1}) == ({"x": 1}, None)


def test_unwrap_julep_meta_preserves_summary_envelope() -> None:
    summary = {"__julep_summary__": "s", "reply": "r"}

    assert _unwrap_julep_meta(summary) == (summary, None)
