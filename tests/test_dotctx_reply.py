"""Tests for Reasoner(reply=...) construction-time schema materialization."""

from __future__ import annotations

from typing import NotRequired, Required, TypedDict

import pytest

from julep.deploy import _reasoner_identity
from julep.dotctx import Reasoner
from julep.ir import SubContract, canonical_json
from julep.kinds import ContextScope, Shape
from julep.registry import DEFAULT_REGISTRY


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


def test_reasoner_replace_is_lossless_and_can_override_every_field() -> None:
    original = Reasoner(
        name="replace.original",
        model="openai:gpt-4o",
        system="system",
        reply=TypedReply,
        tools=("search",),
        temperature=0.25,
        max_rounds=4,
        is_agent=True,
        sub_contract=SubContract(Shape.FEEDBACK),
        context_scope=ContextScope.LOCAL,
        system_render="render.system",
        user_render="render.user",
        max_tokens=512,
        reasoning_effort="high",
        output_retries=2,
        require_tool_call=True,
        response_format="json_object",
        prompt_cache="5m",
    )

    assert original.replace() == original

    replacement = original.replace(
        name="replace.new",
        model="anthropic:claude-sonnet-4",
        system="new system",
        reply={"type": "string"},
        tools=("lookup",),
        temperature=None,
        max_rounds=None,
        is_agent=False,
        sub_contract=None,
        context_scope=ContextScope.WHOLE_SESSION,
        system_render=None,
        user_render=None,
        max_tokens=None,
        reasoning_effort=None,
        output_retries=0,
        require_tool_call=False,
        response_format=None,
        prompt_cache=None,
    )

    assert replacement.name == "replace.new"
    assert replacement.model == "anthropic:claude-sonnet-4"
    assert replacement.system == "new system"
    assert replacement.reply_schema == {"type": "string"}
    assert replacement.tools == ("lookup",)
    assert replacement.temperature is None
    assert replacement.max_rounds is None
    assert replacement.is_agent is False
    assert replacement.sub_contract is None
    assert replacement.context_scope is ContextScope.WHOLE_SESSION
    assert replacement.system_render is None
    assert replacement.user_render is None
    assert replacement.max_tokens is None
    assert replacement.reasoning_effort is None
    assert replacement.output_retries == 0
    assert replacement.require_tool_call is False
    assert replacement.response_format is None
    assert replacement.prompt_cache is None


def test_reasoner_replace_reply_distinguishes_keep_clear_and_rematerialize(
    decision_model: type[object],
) -> None:
    Decision = decision_model
    original = Reasoner("replace.reply", "openai:gpt-4o", reply=TypedReply)

    assert original.replace(model="openai:gpt-4.1").reply_schema == original.reply_schema
    assert original.replace(reply=None).reply_schema is None
    assert original.replace(reply=Decision).reply_schema == Decision.model_json_schema()
