"""Tests for Brain(reply=...) construction-time schema materialization."""

from __future__ import annotations

from typing import NotRequired, Required, TypedDict

import pytest

from composable_agents.deploy import _brain_identity
from composable_agents.dotctx import Brain, register_brain
from composable_agents.ir import canonical_json
from composable_agents.registry import DEFAULT_REGISTRY


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


def _registered_identity(brain: Brain) -> dict[str, object]:
    DEFAULT_REGISTRY.brains.pop(brain.name, None)
    try:
        register_brain(brain)
        return _brain_identity(brain.name)
    finally:
        DEFAULT_REGISTRY.brains.pop(brain.name, None)


def test_reply_model_materializes_to_model_json_schema(decision_model: type[object]) -> None:
    Decision = decision_model
    brain = Brain(name="reply.model", model="openai:gpt-4o", reply=Decision)

    assert brain.reply_schema == Decision.model_json_schema()


def test_reply_model_serializes_identically_to_equivalent_reply_schema(
    decision_model: type[object],
) -> None:
    Decision = decision_model
    schema = Decision.model_json_schema()
    from_reply = _registered_identity(
        Brain(name="reply.model.from_type", model="openai:gpt-4o", reply=Decision)
    )
    from_schema = _registered_identity(
        Brain(name="reply.model.from_schema", model="openai:gpt-4o", reply_schema=schema)
    )

    assert canonical_json({**from_reply, "name": "same"}) == canonical_json(
        {**from_schema, "name": "same"}
    )


def test_reply_and_reply_schema_are_mutually_exclusive(decision_model: type[object]) -> None:
    Decision = decision_model
    with pytest.raises(ValueError, match="reply.*reply_schema"):
        Brain(
            name="reply.both",
            model="openai:gpt-4o",
            reply=Decision,
            reply_schema=Decision.model_json_schema(),
        )


def test_brain_without_reply_keeps_existing_identity_bytes() -> None:
    identity = _registered_identity(Brain(name="reply.none", model="openai:gpt-4o"))

    assert canonical_json(identity) == (
        '{"model":"openai:gpt-4o","name":"reply.none","replySchema":null,'
        '"system":"","tools":[]}'
    )


def test_reply_typeddict_materializes_to_json_schema() -> None:
    brain = Brain(name="reply.typed_dict", model="openai:gpt-4o", reply=TypedReply)

    assert brain.reply_schema == {
        "type": "object",
        "properties": {
            "answer": {"type": "string"},
            "confidence": {"type": "number"},
            "tags": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["answer", "confidence", "tags"],
    }


def test_reply_typeddict_notrequired_field_is_not_required_under_future_annotations() -> None:
    brain = Brain(
        name="reply.typed_dict.not_required",
        model="openai:gpt-4o",
        reply=PartlyOptionalReply,
    )

    assert brain.reply_schema == {
        "type": "object",
        "properties": {
            "answer": {"type": "string"},
            "debug": {"type": "string"},
        },
        "required": ["answer"],
    }


def test_reply_typeddict_required_field_is_required_under_future_annotations() -> None:
    brain = Brain(
        name="reply.typed_dict.required",
        model="openai:gpt-4o",
        reply=PartlyRequiredReply,
    )

    assert brain.reply_schema == {
        "type": "object",
        "properties": {
            "answer": {"type": "string"},
            "route": {"type": "string"},
        },
        "required": ["route"],
    }


def test_reply_typeddict_nested_notrequired_field_resolves_under_future_annotations() -> None:
    brain = Brain(
        name="reply.typed_dict.nested_not_required",
        model="openai:gpt-4o",
        reply=NestedReply,
    )

    assert brain.reply_schema == {
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
        Brain(name="reply.unsupported", model="openai:gpt-4o", reply=object)
