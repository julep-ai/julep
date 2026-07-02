"""Tests for Reasoner(reply=...) construction-time schema materialization."""

from __future__ import annotations

from typing import NotRequired, Required, TypedDict

import pytest

from composable_agents.deploy import _reasoner_identity
from composable_agents.dotctx import Reasoner
from composable_agents.registry import DEFAULT_REGISTRY
from composable_agents.ir import canonical_json


@pytest.fixture
def decision_model() -> type[object]:
    pydantic = pytest.importorskip("pydantic")

    class Decision(pydantic.BaseModel):
        route: str
        confidence: float

    return Decision


class TypedReply(TypedDict):
    answer: str
    confidence: float
    tags: list[str]


class PartlyOptionalReply(TypedDict):
    answer: str
    debug: NotRequired[str]


class PartlyRequiredReply(TypedDict, total=False):
    answer: str
    route: Required[str]


class NestedDetails(TypedDict):
    title: str
    note: NotRequired[str]


class NestedReply(TypedDict):
    details: NestedDetails


def _registered_identity(reasoner: Reasoner) -> dict[str, object]:
    DEFAULT_REGISTRY.reasoners.pop(reasoner.name, None)
    try:
        DEFAULT_REGISTRY.register_reasoner(reasoner)
        return _reasoner_identity(reasoner.name)
    finally:
        DEFAULT_REGISTRY.reasoners.pop(reasoner.name, None)


def test_reply_model_materializes_to_model_json_schema(decision_model: type[object]) -> None:
    Decision = decision_model
    reasoner = Reasoner(name="reply.model", model="openai:gpt-4o", reply=Decision)

    assert reasoner.reply_schema == Decision.model_json_schema()


def test_reply_model_serializes_identically_to_equivalent_reply_schema(
    decision_model: type[object],
) -> None:
    Decision = decision_model
    schema = Decision.model_json_schema()
    from_reply = _registered_identity(
        Reasoner(name="reply.model.from_type", model="openai:gpt-4o", reply=Decision)
    )
    from_schema = _registered_identity(
        Reasoner(name="reply.model.from_schema", model="openai:gpt-4o", reply=schema)
    )

    assert canonical_json({**from_reply, "name": "same"}) == canonical_json(
        {**from_schema, "name": "same"}
    )


def test_reply_accepts_typeddict_and_raw_schema_dict() -> None:
    schema = {"answer": "str"}
    from_type = Reasoner(name="reply.from_type", model="openai:gpt-4o", reply=TypedReply)
    from_schema = Reasoner(name="reply.from_schema", model="openai:gpt-4o", reply=schema)

    assert isinstance(from_type.reply_schema, dict) and from_type.reply_schema
    assert from_schema.reply_schema == schema


def test_reasoner_without_reply_keeps_existing_identity_bytes() -> None:
    identity = _registered_identity(Reasoner(name="reply.none", model="openai:gpt-4o"))

    assert canonical_json(identity) == (
        '{"model":"openai:gpt-4o","name":"reply.none","replySchema":null,'
        '"system":"","tools":[]}'
    )


def test_reasoner_identity_new_phase2_fields_enter_only_when_set() -> None:
    # Omit-when-unset keeps every pre-existing deploy artifact byte-identical.
    unset = _registered_identity(Reasoner(name="rf.unset", model="openai:gpt-4o"))
    assert "requireToolCall" not in unset and "responseFormat" not in unset

    ident = _registered_identity(
        Reasoner(
            name="rf.set", model="openai:gpt-4o",
            require_tool_call=True, response_format="json_object",
        )
    )
    assert ident["requireToolCall"] is True
    assert ident["responseFormat"] == "json_object"


def test_reply_typeddict_materializes_to_json_schema() -> None:
    reasoner = Reasoner(name="reply.typed_dict", model="openai:gpt-4o", reply=TypedReply)

    assert reasoner.reply_schema == {
        "type": "object",
        "properties": {
            "answer": {"type": "string"},
            "confidence": {"type": "number"},
            "tags": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["answer", "confidence", "tags"],
    }


def test_reply_typeddict_notrequired_field_is_not_required_under_future_annotations() -> None:
    reasoner = Reasoner(
        name="reply.typed_dict.not_required",
        model="openai:gpt-4o",
        reply=PartlyOptionalReply,
    )

    assert reasoner.reply_schema == {
        "type": "object",
        "properties": {
            "answer": {"type": "string"},
            "debug": {"type": "string"},
        },
        "required": ["answer"],
    }


def test_reply_typeddict_required_field_is_required_under_future_annotations() -> None:
    reasoner = Reasoner(
        name="reply.typed_dict.required",
        model="openai:gpt-4o",
        reply=PartlyRequiredReply,
    )

    assert reasoner.reply_schema == {
        "type": "object",
        "properties": {
            "answer": {"type": "string"},
            "route": {"type": "string"},
        },
        "required": ["route"],
    }


def test_reply_typeddict_nested_notrequired_field_resolves_under_future_annotations() -> None:
    reasoner = Reasoner(
        name="reply.typed_dict.nested_not_required",
        model="openai:gpt-4o",
        reply=NestedReply,
    )

    assert reasoner.reply_schema == {
        "type": "object",
        "properties": {
            "details": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "note": {"type": "string"},
                },
                "required": ["title"],
            },
        },
        "required": ["details"],
    }


def test_reply_rejects_unsupported_type_with_supported_forms() -> None:
    with pytest.raises(TypeError, match="pydantic.*TypedDict"):
        Reasoner(name="reply.unsupported", model="openai:gpt-4o", reply=object)
