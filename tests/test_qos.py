from __future__ import annotations

import inspect
from enum import Enum

from composable_agents.ir import Ann
from composable_agents.qos import QoSTier, default_resolve_qos


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

    assert list(sig.parameters) == ["brain", "node_ann", "principal", "load"]
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


def test_default_resolve_qos_defaults_to_standard() -> None:
    assert default_resolve_qos(None, Ann(batchable=False), {}) is QoSTier.STANDARD


def test_default_resolve_qos_principal_hint_overrides_default() -> None:
    assert (
        default_resolve_qos(None, Ann(batchable=False), {"qos": "PRIORITY"})
        is QoSTier.PRIORITY
    )
