"""Pure grant-contract helpers lifted from the Temporal harness into
``agent_loop`` so every backend (Temporal, DBOS) shares them. No engine needed.
"""

from __future__ import annotations

from julep.agent_loop import (
    manifest_contracts_for_agent,
    max_call_limits_from_contracts,
)
from julep.contracts import FrozenTool, ToolContract, ToolManifest
from julep.ir import McpTool
from julep.kinds import Effect, Idempotency


def _manifest() -> ToolManifest:
    tools = [
        FrozenTool.create(
            McpTool(server="srv", tool="double"),
            input_schema={},
            contract=ToolContract(effect=Effect.READ, idempotency=Idempotency.NATIVE),
        ),
        FrozenTool.create(
            McpTool(server="srv", tool="inc"),
            input_schema={},
            contract=ToolContract(effect=Effect.WRITE, idempotency=Idempotency.NONE),
        ),
    ]
    return {t.hash: t for t in tools}


def test_manifest_contracts_filters_to_granted() -> None:
    manifest = _manifest()
    contracts = manifest_contracts_for_agent(manifest, ["srv/double"])
    assert set(contracts) == {"srv/double"}
    assert contracts["srv/double"]["effect"] == "read"

    # None means "no filter": every frozen tool's contract is carried.
    everything = manifest_contracts_for_agent(manifest, None)
    assert set(everything) == {"srv/double", "srv/inc"}


def test_manifest_contracts_carries_max_calls() -> None:
    contracts = manifest_contracts_for_agent(
        _manifest(),
        ["srv/double", "srv/inc"],
        max_call_limits={"srv/double": 2},
    )
    assert contracts["srv/double"]["maxCalls"] == 2
    assert "maxCalls" not in contracts["srv/inc"]


def test_max_call_limits_from_contracts_roundtrip() -> None:
    assert max_call_limits_from_contracts(None) is None
    assert max_call_limits_from_contracts({}) is None
    assert max_call_limits_from_contracts({"srv/x": {"effect": "read"}}) is None
    assert max_call_limits_from_contracts(
        {"srv/x": {"maxCalls": 3}, "srv/y": {"max_calls": "4"}, "srv/z": {}}
    ) == {"srv/x": 3, "srv/y": 4}

    # Round-trip: limits stamped by manifest_contracts_for_agent come back out.
    contracts = manifest_contracts_for_agent(
        _manifest(), None, max_call_limits={"srv/double": 1, "srv/inc": 5}
    )
    assert max_call_limits_from_contracts(contracts) == {"srv/double": 1, "srv/inc": 5}


def test_alias_limits_canonicalize_fail_closed() -> None:
    aliases = {"a": "srv/t", "b": "srv/t"}

    assert max_call_limits_from_contracts(
        {"a": {"maxCalls": 3}, "b": {"maxCalls": 2}},
        aliases,
    ) == {"srv/t": 2}
