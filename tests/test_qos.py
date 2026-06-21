from __future__ import annotations

import asyncio
import inspect
from enum import Enum

import pytest

from composable_agents.dotctx import Reasoner
from composable_agents.execution import reasoner_batch, effects
from composable_agents.execution.reasoner_batch import (
    BatchDispatchContext,
    install_batch_dispatch_context,
)
from composable_agents.execution.effects import (
    ResolveQoSInput,
    WorkerContext,
    configure,
    resolveQoS,
)
from composable_agents.ir import Ann
from composable_agents.qos import QoSTier, default_resolve_qos
from composable_agents.registry import Registry


def test_qos_tier_is_str_enum_with_expected_values() -> None:
    assert issubclass(QoSTier, str)
    assert issubclass(QoSTier, Enum)
    assert [tier.name for tier in QoSTier] == [
        "PRIORITY",
        "STANDARD",
        "FLEX",
        "BATCH",
    ]
    assert [tier.value for tier in QoSTier] == [
        "PRIORITY",
        "STANDARD",
        "FLEX",
        "BATCH",
    ]


def test_default_resolve_qos_signature_accepts_load() -> None:
    sig = inspect.signature(default_resolve_qos)

    assert list(sig.parameters) == [
        "reasoner",
        "node_ann",
        "principal",
        "load",
        "timeout_s",
        "min_batch_window_s",
    ]
    assert default_resolve_qos(
        None,
        Ann(batchable=False),
        {},
        load={"pressure": "ignored"},
    ) is QoSTier.STANDARD


def test_default_resolve_qos_clamps_batch_when_node_is_not_batchable() -> None:
    resolved = default_resolve_qos(
        None,
        Ann(batchable=False),
        {"qos": "BATCH"},
    )

    assert resolved is not QoSTier.BATCH
    assert resolved is QoSTier.FLEX


def test_default_resolve_qos_allows_batch_when_node_is_batchable() -> None:
    assert (
        default_resolve_qos(None, Ann(batchable=True), {"qos": "BATCH"})
        is QoSTier.BATCH
    )


def test_default_resolve_qos_predictively_promotes_batch_when_timeout_is_short() -> None:
    resolved = default_resolve_qos(
        None,
        Ann(batchable=True),
        {"qos": "BATCH"},
        timeout_s=9.0,
        min_batch_window_s=10.0,
    )

    assert resolved is QoSTier.FLEX


def test_default_resolve_qos_allows_batch_when_timeout_meets_min_window() -> None:
    assert (
        default_resolve_qos(
            None,
            Ann(batchable=True),
            {"qos": "BATCH"},
            timeout_s=10.0,
            min_batch_window_s=10.0,
        )
        is QoSTier.BATCH
    )


def test_default_resolve_qos_allows_batch_when_timeout_is_unbounded() -> None:
    assert (
        default_resolve_qos(
            None,
            Ann(batchable=True),
            {"qos": "BATCH"},
            timeout_s=None,
            min_batch_window_s=10.0,
        )
        is QoSTier.BATCH
    )


def test_default_resolve_qos_allows_batch_when_min_window_is_unspecified() -> None:
    assert (
        default_resolve_qos(
            None,
            Ann(batchable=True),
            {"qos": "BATCH"},
            timeout_s=1.0,
            min_batch_window_s=None,
        )
        is QoSTier.BATCH
    )


def test_resolve_qos_activity_predictively_clamps_installed_batch_window(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = Registry()
    registry.register_reasoner(Reasoner(name="qos.activity", model="test", system="s"))
    prev_ctx = effects._CTX

    monkeypatch.setattr(reasoner_batch, "_BATCH_CTX", None)
    install_batch_dispatch_context(
        BatchDispatchContext(
            client=object(),
            max_wait_s=60.0,
            min_batch_window_s=10.0,
        )
    )
    configure(WorkerContext(registry=registry))
    try:
        resolved = asyncio.run(
            resolveQoS(
                ResolveQoSInput(
                    reasoner="qos.activity",
                    node_batchable=True,
                    node_id="n1",
                    timeout_s=5.0,
                    principal={"qos": "BATCH"},
                )
            )
        )
    finally:
        effects._CTX = prev_ctx

    assert resolved == QoSTier.FLEX.value


def test_resolve_qos_activity_enforces_non_batchable_floor_after_custom_resolver(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = Registry()
    registry.register_reasoner(Reasoner(name="qos.floor", model="test", system="s"))
    prev_ctx = effects._CTX
    seen_batchable: list[bool] = []

    def resolver(reasoner: object, ann: object, principal: object) -> QoSTier:
        del reasoner, principal
        seen_batchable.append(bool(getattr(ann, "batchable", False)))
        return QoSTier.BATCH

    monkeypatch.setattr(reasoner_batch, "_BATCH_CTX", None)
    configure(WorkerContext(registry=registry, resolve_qos=resolver))
    try:
        non_batchable = asyncio.run(
            resolveQoS(
                ResolveQoSInput(
                    reasoner="qos.floor",
                    node_batchable=False,
                    principal={"qos": "BATCH"},
                )
            )
        )
        batchable = asyncio.run(
            resolveQoS(
                ResolveQoSInput(
                    reasoner="qos.floor",
                    node_batchable=True,
                    principal={"qos": "BATCH"},
                )
            )
        )
    finally:
        effects._CTX = prev_ctx

    assert non_batchable == QoSTier.FLEX.value
    assert batchable == QoSTier.BATCH.value
    assert seen_batchable == [False, True]


def test_resolve_qos_activity_tolerates_resolver_with_partial_kwargs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # A custom resolver that accepts only ``timeout_s`` (not ``min_batch_window_s``)
    # must not raise: the activity passes only the kwargs the resolver declares.
    registry = Registry()
    registry.register_reasoner(Reasoner(name="qos.partial", model="test", system="s"))
    prev_ctx = effects._CTX
    seen: dict[str, object] = {}

    def resolver(reasoner: object, ann: object, principal: object, *, timeout_s: object = None) -> QoSTier:
        seen["timeout_s"] = timeout_s
        return QoSTier.BATCH

    monkeypatch.setattr(reasoner_batch, "_BATCH_CTX", None)
    install_batch_dispatch_context(
        BatchDispatchContext(client=object(), min_batch_window_s=10.0)
    )
    configure(WorkerContext(registry=registry, resolve_qos=resolver))
    try:
        resolved = asyncio.run(
            resolveQoS(
                ResolveQoSInput(
                    reasoner="qos.partial",
                    node_batchable=True,
                    timeout_s=1.0,
                    principal={"qos": "BATCH"},
                )
            )
        )
    finally:
        effects._CTX = prev_ctx

    assert resolved == QoSTier.BATCH.value
    assert seen["timeout_s"] == 1.0


def test_resolve_qos_activity_tolerates_legacy_resolver(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # A legacy 3-positional resolver (no predictive kwargs) must still work.
    registry = Registry()
    registry.register_reasoner(Reasoner(name="qos.legacy", model="test", system="s"))
    prev_ctx = effects._CTX

    def legacy(reasoner: object, ann: object, principal: object) -> QoSTier:
        return QoSTier.STANDARD

    monkeypatch.setattr(reasoner_batch, "_BATCH_CTX", None)
    install_batch_dispatch_context(
        BatchDispatchContext(client=object(), min_batch_window_s=10.0)
    )
    configure(WorkerContext(registry=registry, resolve_qos=legacy))
    try:
        resolved = asyncio.run(
            resolveQoS(
                ResolveQoSInput(
                    reasoner="qos.legacy",
                    node_batchable=True,
                    timeout_s=1.0,
                    principal={"qos": "BATCH"},
                )
            )
        )
    finally:
        effects._CTX = prev_ctx

    assert resolved == QoSTier.STANDARD.value


def test_default_resolve_qos_defaults_to_standard() -> None:
    assert default_resolve_qos(None, Ann(batchable=False), {}) is QoSTier.STANDARD


def test_default_resolve_qos_principal_hint_overrides_default() -> None:
    assert (
        default_resolve_qos(None, Ann(batchable=False), {"qos": "PRIORITY"})
        is QoSTier.PRIORITY
    )
