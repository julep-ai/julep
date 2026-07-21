from __future__ import annotations

from typing import Any

import pytest

from julep import arr, freeze, is_registered
from julep.execution.interpreter import InMemoryEnv, interpret
from julep.projection import InMemoryProjection, ProjectionEmitter
from julep.purity import source_hash_of
from conftest import read_snapshot, run


STD_PURES = (
    "std.merge",
    "std.pluck",
    "std.init",
    "std.assign",
    "std.collect",
    "std.pack",
    "std.unpack",
    "std.bind",
    "std.record",
    "std.each_pack",
    "std.branch_predicate",
    "std.branch_selector",
    "std.continue_with",
)


# WARNING: std pure source hashes are replay pins. Changing any body changes
# replay behavior for every artifact that references that std name. Deliberate
# std behavior changes must register a new name rather than editing the old body.
EXPECTED_STD_SOURCE_HASHES = {
    "std.merge": "pure:f629aa6a7d45f210",
    "std.pluck": "pure:29fc760c408afde4",
    "std.init": "pure:7b74da9294bdf489",
    "std.assign": "pure:e844f98f93635b01",
    "std.collect": "pure:ff671d8f4dcc85a4",
    "std.pack": "pure:9a0d3873bbef3f97",
    "std.unpack": "pure:82b536c49d7cee7e",
    "std.bind": "pure:9936960359bdf9a3",
    "std.record": "pure:5cbff8464f82262f",
    "std.each_pack": "pure:d40a26dcb92b73a8",
    "std.branch_predicate": "pure:bee903d8d036cbe7",
    "std.branch_selector": "pure:a65863c731e19705",
    "std.continue_with": "pure:1fcb10b5d8eef05d",
}


def _run_std(name: str, value: Any, args: dict[str, Any] | None = None) -> Any:
    frozen = freeze(arr(name, args=args), read_snapshot())
    env = InMemoryEnv(
        frozen.manifest,
        ProjectionEmitter(InMemoryProjection()),
    )
    return run(interpret(frozen.flow, value, env)).value


def test_std_family_is_registered_at_package_import_and_source_hash_pinned() -> None:
    for name in STD_PURES:
        assert is_registered(name)

    assert {name: source_hash_of(name) for name in STD_PURES} == EXPECTED_STD_SOURCE_HASHES


def test_std_pluck_projects_one_key_and_missing_key_is_loud() -> None:
    assert _run_std("std.pluck", {"summary": "ok", "other": 1}, {"key": "summary"}) == "ok"

    with pytest.raises(KeyError, match="'summary'"):
        _run_std("std.pluck", {"other": 1}, {"key": "summary"})


def test_std_init_and_assign_are_distinct_without_shape_sniffing() -> None:
    env = {"episode_id": "ep-1"}
    pair_input = [env, {"summary": "done"}]

    assert _run_std("std.init", pair_input, {"key": "summary"}) == {"summary": pair_input}
    assert _run_std("std.assign", pair_input, {"key": "summary"}) == {
        "episode_id": "ep-1",
        "summary": {"summary": "done"},
    }
    assert env == {"episode_id": "ep-1"}


def test_std_collect_extends_env_from_multi_result_par_layout() -> None:
    env = {"source": {"episode_id": "ep-1"}}
    value = [env, {"summary": "done"}, {"embedding": [4, 8]}]

    assert _run_std("std.collect", value, {"fields": ["summary", "embedding"]}) == {
        "source": {"episode_id": "ep-1"},
        "summary": {"summary": "done"},
        "embedding": {"embedding": [4, 8]},
    }
    assert env == {"source": {"episode_id": "ep-1"}}

    with pytest.raises(ValueError, match="std.collect expected 3 values, got 2"):
        _run_std("std.collect", [env, {"summary": "done"}], {"fields": ["summary", "embedding"]})


def test_std_merge_binary_pair_uses_right_wins_dict_union() -> None:
    assert _run_std("std.merge", [{"a": 1, "same": "left"}, {"b": 2, "same": "right"}]) == {
        "a": 1,
        "same": "right",
        "b": 2,
    }


def test_std_merge_field_list_projects_env_fields_in_order_with_right_wins() -> None:
    env = {
        "label_source": {"cluster_id": "c1", "label": "fallback"},
        "label": {"label": "Memory cluster"},
        "keywords": {"keywords": ["Ada", "Ben"]},
        "unused": {"ignored": True},
    }

    assert _run_std(
        "std.merge",
        env,
        {"fields": ["label_source", "label", "keywords"]},
    ) == {
        "cluster_id": "c1",
        "label": "Memory cluster",
        "keywords": ["Ada", "Ben"],
    }


def test_std_pack_and_unpack_named_record_mapping_round_trip() -> None:
    input_env = {
        "store_context": {"store_id": "s1"},
        "item": {"cluster_id": "c1"},
        "extra": "ignored",
    }

    packed = _run_std(
        "std.pack",
        input_env,
        {
            "fields": {
                "context": {"field": "store_context"},
                "cluster": {"field": "item"},
                "limit": {"const": 3},
            }
        },
    )
    assert packed == {
        "context": {"store_id": "s1"},
        "cluster": {"cluster_id": "c1"},
        "limit": 3,
    }

    assert _run_std(
        "std.unpack",
        packed,
        {"fields": {"store_context": "context", "item": "cluster", "limit": "limit"}},
    ) == {
        "store_context": {"store_id": "s1"},
        "item": {"cluster_id": "c1"},
        "limit": 3,
    }


def test_std_pack_can_name_the_whole_flowing_input() -> None:
    assert _run_std(
        "std.pack",
        {"cluster_id": "c1"},
        {"fields": {"cluster": {"input": True}, "store_context": {"const": {"store_id": "s1"}}}},
    ) == {"cluster": {"cluster_id": "c1"}, "store_context": {"store_id": "s1"}}


def test_std_bind_merges_consts_and_rejects_collisions_deterministically() -> None:
    assert _run_std("std.bind", {"episode_id": "ep-1"}, {"consts": {"limit": 10}}) == {
        "episode_id": "ep-1",
        "limit": 10,
    }

    with pytest.raises(ValueError, match="std.bind key collision: limit, store_id"):
        _run_std(
            "std.bind",
            {"limit": 5, "store_id": "s1"},
            {"consts": {"store_id": "s2", "limit": 10}},
        )


def test_std_record_builds_named_values_consts_and_deduplicated_aliases() -> None:
    assert _run_std(
        "std.record",
        [{"id": "c1"}, "needle"],
        {
            "fields": [
                ["collection", 0],
                ["query", 1],
                ["same_collection", 0],
                ["limit", None],
            ],
            "consts": {"limit": 10},
        },
    ) == {
        "collection": {"id": "c1"},
        "same_collection": {"id": "c1"},
        "query": "needle",
        "limit": 10,
    }

    assert _run_std(
        "std.record",
        ["one", "value"],
        {"fields": [["items", 0]], "consts": {}},
    ) == {"items": ["one", "value"]}

    with pytest.raises(ValueError, match="std.record expected 2 values, got 1"):
        _run_std(
            "std.record",
            ["only-one"],
            {"fields": [["first", 0], ["second", 1]], "consts": {}},
        )


def test_std_each_pack_maps_items_with_handle_fields_and_consts() -> None:
    assert _run_std(
        "std.each_pack",
        {"clusters": [{"id": "c1"}, {"id": "c2"}], "store_context": {"store_id": "s1"}},
        {
            "items": "clusters",
            "item": "cluster",
            "fields": {"store_context": "store_context"},
            "consts": {"model": "small"},
        },
    ) == [
        {"cluster": {"id": "c1"}, "store_context": {"store_id": "s1"}, "model": "small"},
        {"cluster": {"id": "c2"}, "store_context": {"store_id": "s1"}, "model": "small"},
    ]


def test_std_branch_pures_read_internal_branch_value() -> None:
    assert _run_std("std.branch_predicate", {"__branch__": 1}) is True
    assert _run_std("std.branch_predicate", {"__branch__": 0}) is False
    assert _run_std("std.branch_selector", {"__branch__": "success"}) == "success"


def test_std_continue_with_wraps_continuation_sentinel() -> None:
    assert _run_std("std.continue_with", {"cursor": 10}) == {"__continue__": {"cursor": 10}}
