from __future__ import annotations

import warnings
from typing import Any

import pytest

from composable_agents import dsl, pure
from composable_agents.contracts import ToolContract
from composable_agents.execution.interpreter import InMemoryEnv, interpret
from composable_agents.ir import Node, SourceSpan, canonical_json
from composable_agents.kinds import Effect, Idempotency, Op
from composable_agents.projection import InMemoryProjection, ProjectionEmitter
from composable_agents.transforms import normalize_ids
from conftest import run


def _canonical_ir(node: Node) -> str:
    return canonical_json(normalize_ids(Node.from_json(node.to_json())).to_json())


def _seq_items(node: Node) -> list[Node]:
    if node.op is not Op.SEQ:
        return [node]
    items: list[Node] = []
    if node.left is not None:
        items.extend(_seq_items(node.left))
    if node.right is not None:
        items.extend(_seq_items(node.right))
    return items


def _is_std_arr(node: Node, pure: str, args: dict[str, Any]) -> bool:
    return node.op is Op.ARR and node.pure == pure and node.args == args


def _assert_no_assign_then_same_key_pluck(node: Node) -> None:
    for seq_node in node.walk():
        if seq_node.op is not Op.SEQ:
            continue
        seq_items = _seq_items(seq_node)
        for left, right in zip(seq_items, seq_items[1:], strict=False):
            if left.pure == "std.assign" and right.pure == "std.pluck":
                assert left.args != right.args


DEAD_ASSIGN_ENV_FOLD_BACK_NOTE = (
    "A write-barrier layer whose result is not live still needs std.assign before "
    "liveness pruning: std.assign is the existing std-family fold-back from "
    "[env, side_effect_result] to env, and eliding it would require a new "
    "wire-format-stable std pure."
)


READ_CONTRACT = ToolContract(effect=Effect.READ, idempotency=Idempotency.NATIVE)
WRITE_CONTRACT = ToolContract(effect=Effect.WRITE, idempotency=Idempotency.NONE)


@pure("dag.is_found")
def dag_is_found(env: dict[str, Any]) -> bool:
    return bool(env["source"].get("found"))


@pure("dag.status_selector")
def dag_status_selector(env: dict[str, Any]) -> str:
    return str(env["status"]["status"])


@pure("dag.missing_result")
def dag_missing_result(source: dict[str, Any]) -> dict[str, Any]:
    return {"status": "not_found", "episode_id": source["episode_id"]}


@pure("dag.case_success")
def dag_case_success(status: dict[str, Any]) -> dict[str, Any]:
    return {"handled": "success", "episode_id": status["episode_id"]}


@pure("dag.case_stale")
def dag_case_stale(status: dict[str, Any]) -> dict[str, Any]:
    return {"handled": "stale", "episode_id": status["episode_id"]}


@pure("dag.case_missing")
def dag_case_missing(status: dict[str, Any]) -> dict[str, Any]:
    return {"handled": "missing", "episode_id": status["episode_id"]}


@pure("dag.case_default")
def dag_case_default(status: dict[str, Any]) -> dict[str, Any]:
    return {"handled": "default", "episode_id": status["episode_id"]}


@pure("dag.decorate_decision")
def dag_decorate_decision(decision: dict[str, Any]) -> dict[str, Any]:
    decorated = dict(decision)
    decorated["decorated"] = True
    return decorated


@pure("dag.input_identity")
def dag_input_identity(value: dict[str, Any]) -> dict[str, Any]:
    return {"input": value["episode_id"]}


@pure("dag.process_source")
def dag_process_source(value: dict[str, Any]) -> dict[str, Any]:
    return {"proc": value["episode_id"]}


@pure("dag.combine_input_and_wrote")
def dag_combine_input_and_wrote(value: dict[str, Any]) -> dict[str, Any]:
    return {"input": value["episode_id"], "wrote": value["wrote"]}


@pure("dag.combine_input_and_proc")
def dag_combine_input_and_proc(value: dict[str, Any]) -> dict[str, Any]:
    return {"input": value["episode_id"], "proc": value["proc"]}


@pure("dag.branch_true_from_source")
def dag_branch_true_from_source(value: dict[str, Any]) -> dict[str, Any]:
    return {"branch": "true", "episode_id": value["episode_id"]}


@pure("dag.branch_false_const")
def dag_branch_false_const(value: dict[str, Any]) -> dict[str, Any]:
    return {"branch": "false"}


@pure("dag.input_flag")
def dag_input_flag(value: dict[str, Any]) -> bool:
    return bool(value["__input__"]["found"])


@pure("dag.branch_from_input")
def dag_branch_from_input(value: dict[str, Any]) -> dict[str, Any]:
    return {"branch": value["episode_id"]}


@pure("dag.make_cluster_label")
def dag_make_cluster_label(value: dict[str, Any]) -> dict[str, Any]:
    return {
        "store_id": value["store_id"],
        "cluster_id": value["cluster_id"],
        "label": f"{value['prefix']}:{value['cluster_id']}",
        "expected_revision": value["revision"],
    }


@pure("dag.attach_const_model")
def dag_attach_const_model(value: dict[str, Any]) -> dict[str, Any]:
    return dict(value)


@pure("dag.cluster_count")
def dag_cluster_count(value: list[dict[str, Any]]) -> dict[str, int]:
    return {"cluster_count": len(value)}


@pure("dag.tally_cluster_statuses")
def dag_tally_cluster_statuses(statuses: list[dict[str, Any]]) -> dict[str, int]:
    tally = {"success": 0, "stale": 0}
    for status in statuses:
        if status["status"] == "success":
            tally["success"] += 1
        elif status["status"] == "stale_source":
            tally["stale"] += 1
    return tally


def test_linear_chain_compiles_without_env_record_shims() -> None:
    from composable_agents.dag import Graph, StepKind, compile

    graph = Graph()
    graph.add_step(StepKind.TOOL, "read_episode", output="source", contract=READ_CONTRACT)
    graph.add_step(StepKind.THINK, "summarizer", inputs=["source"], output="summary")
    graph.add_step(StepKind.PURE, "format_summary", inputs=["summary"], output="formatted")

    expected = dsl.seq(
        dsl.call("read_episode"),
        dsl.think("summarizer"),
        dsl.arr("format_summary"),
    )

    assert _canonical_ir(compile(graph)) == _canonical_ir(expected)


def test_diamond_fan_in_compiles_to_minimal_parallel_env_flow() -> None:
    from composable_agents.dag import Graph, StepKind, compile

    graph = Graph()
    graph.add_step(StepKind.TOOL, "read_episode", output="source", contract=READ_CONTRACT)
    graph.add_step(StepKind.THINK, "summarizer", inputs=["source"], output="summary")
    graph.add_step(StepKind.THINK, "embedder", inputs=["source"], output="embedding")
    graph.add_step(
        StepKind.TOOL,
        "write_summary",
        inputs=["source", "summary", "embedding"],
        output="status",
        contract=WRITE_CONTRACT,
    )

    compiled = compile(graph)
    expected = dsl.seq(
        dsl.call("read_episode"),
        dsl.arr("std.init", {"key": "source"}),
        dsl.par(
            dsl.ident(),
            dsl.seq(dsl.arr("std.pluck", {"key": "source"}), dsl.think("summarizer")),
            dsl.seq(dsl.arr("std.pluck", {"key": "source"}), dsl.think("embedder")),
        ),
        dsl.arr("std.collect", {"fields": ["summary", "embedding"]}),
        dsl.arr("std.merge", {"fields": ["source", "summary", "embedding"]}),
        dsl.call("write_summary"),
    )

    _assert_no_assign_then_same_key_pluck(compiled)
    assert _canonical_ir(compiled) == _canonical_ir(expected)


def test_authored_std_merge_multi_input_collapses_to_env_projection_only() -> None:
    from composable_agents.dag import Graph, StepKind, compile

    graph = Graph()
    graph.add_step(StepKind.TOOL, "produce_a", output="a", contract=READ_CONTRACT)
    graph.add_step(StepKind.TOOL, "produce_b", output="b", contract=READ_CONTRACT)
    graph.add_step(StepKind.PURE, "std.merge", inputs=["a", "b"], output="merged")
    graph.add_step(
        StepKind.TOOL,
        "consume_merged",
        inputs=["merged"],
        output="status",
        contract=WRITE_CONTRACT,
    )

    compiled = compile(graph)
    expected = dsl.seq(
        dsl.arr("std.init", {"key": "__input__"}),
        dsl.par(
            dsl.ident(),
            dsl.seq(dsl.arr("std.pluck", {"key": "__input__"}), dsl.call("produce_a")),
            dsl.seq(dsl.arr("std.pluck", {"key": "__input__"}), dsl.call("produce_b")),
        ),
        dsl.arr("std.collect", {"fields": ["a", "b"]}),
        dsl.arr("std.pack", {"fields": {"a": {"field": "a"}, "b": {"field": "b"}}}),
        dsl.par(
            dsl.ident(),
            dsl.arr("std.merge", {"fields": ["a", "b"]}),
        ),
        dsl.arr("std.assign", {"key": "merged"}),
        dsl.arr("std.pluck", {"key": "merged"}),
        dsl.call("consume_merged"),
    )

    merge_nodes = [
        node for node in compiled.walk() if node.op is Op.ARR and node.pure == "std.merge"
    ]
    assert [node.args for node in merge_nodes] == [{"fields": ["a", "b"]}]
    assert _canonical_ir(compiled) == _canonical_ir(expected)


def test_nested_binary_merge_chain_compiles_as_declared_and_runs() -> None:
    from composable_agents.dag import Graph, StepKind, compile

    graph = Graph()
    graph.add_step(StepKind.TOOL, "produce_a", output="a", contract=READ_CONTRACT)
    graph.add_step(StepKind.TOOL, "produce_b", output="b", contract=READ_CONTRACT)
    graph.add_step(StepKind.TOOL, "produce_c", output="c", contract=READ_CONTRACT)
    graph.add_step(StepKind.PURE, "std.merge", inputs=["a", "b"], output="m1")
    graph.add_step(StepKind.PURE, "std.merge", inputs=["m1", "c"], output="m2")

    compiled = compile(graph)
    expected = dsl.seq(
        dsl.arr("std.init", {"key": "__input__"}),
        dsl.par(
            dsl.ident(),
            dsl.seq(dsl.arr("std.pluck", {"key": "__input__"}), dsl.call("produce_a")),
            dsl.seq(dsl.arr("std.pluck", {"key": "__input__"}), dsl.call("produce_b")),
            dsl.seq(dsl.arr("std.pluck", {"key": "__input__"}), dsl.call("produce_c")),
        ),
        dsl.arr("std.collect", {"fields": ["a", "b", "c"]}),
        dsl.arr(
            "std.pack",
            {"fields": {"a": {"field": "a"}, "b": {"field": "b"}, "c": {"field": "c"}}},
        ),
        dsl.par(
            dsl.ident(),
            dsl.arr("std.merge", {"fields": ["a", "b"]}),
        ),
        dsl.arr("std.assign", {"key": "m1"}),
        dsl.arr("std.pack", {"fields": {"c": {"field": "c"}, "m1": {"field": "m1"}}}),
        dsl.arr("std.merge", {"fields": ["m1", "c"]}),
    )

    merge_args = [
        node.args
        for node in compiled.walk()
        if node.op is Op.ARR and node.pure == "std.merge"
    ]
    assert merge_args == [{"fields": ["a", "b"]}, {"fields": ["m1", "c"]}]
    assert _canonical_ir(compiled) == _canonical_ir(expected)

    def produce_a(value: dict[str, Any]) -> dict[str, Any]:
        return {"a": value["seed"], "shared": "a"}

    def produce_b(value: dict[str, Any]) -> dict[str, Any]:
        return {"b": value["seed"], "shared": "b"}

    def produce_c(value: dict[str, Any]) -> dict[str, Any]:
        return {"c": value["seed"], "shared": "c"}

    env = InMemoryEnv(
        {},
        ProjectionEmitter(InMemoryProjection()),
        tools={"produce_a": produce_a, "produce_b": produce_b, "produce_c": produce_c},
    )

    result = run(interpret(compiled, {"seed": "s1"}, env))

    assert result.value == {"a": "s1", "b": "s1", "c": "s1", "shared": "c"}


def test_write_barrier_keeps_later_read_sequential() -> None:
    from composable_agents.dag import Graph, StepKind, compile

    graph = Graph()
    graph.add_step(StepKind.TOOL, "read_before", output="source", contract=READ_CONTRACT)
    graph.add_step(
        StepKind.TOOL,
        "write_status",
        inputs=["source"],
        output="write_result",
        contract=WRITE_CONTRACT,
    )
    graph.add_step(StepKind.TOOL, "read_after", inputs=["source"], output="after", contract=READ_CONTRACT)

    compiled = compile(graph)
    expected = dsl.seq(
        dsl.call("read_before"),
        dsl.arr("std.init", {"key": "source"}),
        dsl.par(
            dsl.ident(),
            dsl.seq(dsl.arr("std.pluck", {"key": "source"}), dsl.call("write_status")),
        ),
        dsl.arr("std.assign", {"key": "write_result"}),
        dsl.arr("std.pluck", {"key": "source"}),
        dsl.call("read_after"),
    )

    assert "write-barrier layer" in DEAD_ASSIGN_ENV_FOLD_BACK_NOTE
    _assert_no_assign_then_same_key_pluck(compiled)
    assert _canonical_ir(compiled) == _canonical_ir(expected)


def test_compiled_diamond_runs_end_to_end() -> None:
    from composable_agents.dag import Graph, StepKind, compile

    graph = Graph()
    graph.add_step(StepKind.TOOL, "read_episode", output="source", contract=READ_CONTRACT)
    graph.add_step(StepKind.THINK, "summarizer", inputs=["source"], output="summary")
    graph.add_step(StepKind.THINK, "embedder", inputs=["source"], output="embedding")
    graph.add_step(
        StepKind.TOOL,
        "write_summary",
        inputs=["source", "summary", "embedding"],
        output="status",
        contract=WRITE_CONTRACT,
    )

    def read_episode(value: dict[str, Any]) -> dict[str, Any]:
        return {"episode_id": value["episode_id"], "text": "Ada met Ben."}

    def summarizer(value: dict[str, Any]) -> dict[str, Any]:
        return {"summary": value["text"]}

    def embedder(value: dict[str, Any]) -> dict[str, Any]:
        return {"embedding": [len(value["text"])]}

    def write_summary(value: dict[str, Any]) -> dict[str, Any]:
        return {
            "status": "success",
            "episode_id": value["episode_id"],
            "summary": value["summary"],
            "embedding": value["embedding"],
        }

    env = InMemoryEnv(
        {},
        ProjectionEmitter(InMemoryProjection()),
        tools={"read_episode": read_episode, "write_summary": write_summary},
        reasoners={"summarizer": summarizer, "embedder": embedder},
    )

    result = run(interpret(compile(graph), {"episode_id": "ep-1"}, env))

    assert result.value == {
        "status": "success",
        "episode_id": "ep-1",
        "summary": "Ada met Ben.",
        "embedding": [12],
    }


def test_graph_rejects_output_name_collisions_at_definition_time() -> None:
    from composable_agents.dag import Graph, GraphDefinitionError, StepKind

    graph = Graph()
    graph.add_step(StepKind.PURE, "one", output="value")

    with pytest.raises(GraphDefinitionError, match="output name collision: value"):
        graph.add_step(StepKind.PURE, "two", output="value")


def test_graph_explicit_output_name_is_not_clobbered_by_add_step() -> None:
    from composable_agents.dag import Graph, StepKind

    graph = Graph(output_name="first")
    graph.add_step(StepKind.PURE, "one", output="first")
    graph.add_step(StepKind.PURE, "two", inputs=["first"], output="second")

    assert graph.output_name == "first"


def test_compile_rejects_cycles_and_names_cycle_members() -> None:
    from composable_agents.dag import Graph, GraphDefinitionError, StepKind, compile

    graph = Graph()
    graph.add_step(StepKind.PURE, "first", inputs=["second"], output="first")
    graph.add_step(StepKind.PURE, "second", inputs=["first"], output="second")

    with pytest.raises(GraphDefinitionError, match="cycle.*first.*second"):
        compile(graph)


def test_compile_rejects_explicit_unknown_output_name_before_runtime() -> None:
    from composable_agents.dag import Graph, GraphDefinitionError, StepKind, compile

    span = SourceSpan("flow.py", 12, "build", "return typo")
    graph = Graph(output_name="typo", source=span)
    graph.add_step(StepKind.TOOL, "read_episode", output="source", contract=READ_CONTRACT)
    graph.add_step(StepKind.PURE, "dag.process_source", inputs=["source"], output="processed")

    with pytest.raises(
        GraphDefinitionError,
        match=(
            r"unknown output name: typo.*flow.py:12.*"
            r"available outputs: processed, source.*return one of the available handles"
        ),
    ):
        compile(graph)


def test_user_input_edge_rename_is_rejected_at_definition_time() -> None:
    from composable_agents.dag import Graph, GraphDefinitionError, InputEdge, StepKind

    span = SourceSpan("flow.py", 22, "build", "renamed = consume(source)")
    graph = Graph()
    graph.add_step(StepKind.TOOL, "read_episode", output="source", contract=READ_CONTRACT)

    with pytest.raises(
        GraphDefinitionError,
        match=(
            r"input edge renaming is not supported.*flow.py:22.*"
            r"name='renamed'.*source='source'.*use inputs=\['source'\]"
        ),
    ):
        graph.add_step(
            StepKind.PURE,
            "dag.process_source",
            inputs=[InputEdge(name="renamed", source="source")],
            output="processed",
            source=span,
        )


def test_add_each_internal_items_edge_is_still_allowed_after_rename_rejection() -> None:
    from composable_agents.dag import Graph, StepKind, compile

    body = Graph(input_name="cluster", output_name="copied")
    body.add_step(StepKind.PURE, "dag.branch_from_input", output="copied")

    graph = Graph()
    graph.add_step(StepKind.TOOL, "read_items", output="items", contract=READ_CONTRACT)
    graph.add_each(body, items="items", output="copied")

    assert compile(graph).op is Op.SEQ


def test_compile_rejects_forward_referenced_edges_across_write_barriers() -> None:
    from composable_agents.dag import Graph, GraphDefinitionError, StepKind, compile

    graph = Graph()
    graph.add_step(StepKind.PURE, "dag.input_identity", inputs=["late_read"], output="pure_result")
    graph.add_step(
        StepKind.TOOL,
        "cas_write",
        output="write_result",
        contract=WRITE_CONTRACT,
    )
    graph.add_step(
        StepKind.TOOL,
        "verify_read",
        output="late_read",
        contract=READ_CONTRACT,
    )

    with pytest.raises(
        GraphDefinitionError,
        match="forward input edge.*pure_result.*late_read.*dependency order",
    ):
        compile(graph)

    two_writes = Graph()
    two_writes.add_step(
        StepKind.TOOL,
        "write_two",
        inputs=["write_one_result"],
        output="write_two_result",
        contract=WRITE_CONTRACT,
    )
    two_writes.add_step(
        StepKind.TOOL,
        "write_one",
        output="write_one_result",
        contract=WRITE_CONTRACT,
    )

    with pytest.raises(
        GraphDefinitionError,
        match="forward input edge.*write_two_result.*write_one_result.*dependency order",
    ):
        compile(two_writes)

    ordered = Graph()
    ordered.add_step(
        StepKind.TOOL,
        "write_one",
        output="write_one_result",
        contract=WRITE_CONTRACT,
    )
    ordered.add_step(
        StepKind.TOOL,
        "write_two",
        inputs=["write_one_result"],
        output="write_two_result",
        contract=WRITE_CONTRACT,
    )

    assert compile(ordered).op is Op.SEQ


def test_singleton_first_layer_preserves_raw_input_for_later_declared_consumer() -> None:
    from composable_agents.dag import Graph, StepKind, compile

    graph = Graph()
    graph.add_step(StepKind.TOOL, "read_episode", output="source", contract=READ_CONTRACT)
    graph.add_step(
        StepKind.TOOL,
        "write_status",
        inputs=["source"],
        output="wrote",
        contract=WRITE_CONTRACT,
    )
    graph.add_step(StepKind.PURE, "dag.input_identity", inputs=["__input__"], output="result")

    calls: list[str] = []

    def read_episode(value: dict[str, Any]) -> dict[str, Any]:
        calls.append("read")
        return {"episode_id": value["episode_id"]}

    def write_status(value: dict[str, Any]) -> dict[str, Any]:
        calls.append("write")
        return {"wrote": value["episode_id"]}

    compiled = compile(graph)
    compiled_json = _canonical_ir(compiled)
    write_index = compiled_json.index('"name":"write_status"')
    result_index = compiled_json.index('"pure":"dag.input_identity"')
    assert write_index < result_index

    env = InMemoryEnv(
        {},
        ProjectionEmitter(InMemoryProjection()),
        tools={"read_episode": read_episode, "write_status": write_status},
    )

    result = run(interpret(compiled, {"episode_id": "ep-1"}, env))

    assert calls == ["read", "write"]
    assert result.value == {"input": "ep-1"}


def test_singleton_first_layer_preserves_raw_input_for_later_implicit_consumer() -> None:
    from composable_agents.dag import Graph, StepKind, compile

    graph = Graph()
    graph.add_step(StepKind.TOOL, "read_episode", output="source", contract=READ_CONTRACT)
    graph.add_step(
        StepKind.TOOL,
        "write_status",
        inputs=["source"],
        output="wrote",
        contract=WRITE_CONTRACT,
    )
    graph.add_step(StepKind.TOOL, "verify_read", output="verified", contract=READ_CONTRACT)

    observed: list[dict[str, Any]] = []

    def read_episode(value: dict[str, Any]) -> dict[str, Any]:
        return {"episode_id": value["episode_id"]}

    def write_status(value: dict[str, Any]) -> dict[str, Any]:
        return {"wrote": value["episode_id"]}

    def verify_read(value: dict[str, Any]) -> dict[str, Any]:
        observed.append(value)
        return {"verified": value["episode_id"]}

    env = InMemoryEnv(
        {},
        ProjectionEmitter(InMemoryProjection()),
        tools={
            "read_episode": read_episode,
            "write_status": write_status,
            "verify_read": verify_read,
        },
    )

    result = run(interpret(compile(graph), {"episode_id": "ep-1"}, env))

    assert observed == [{"episode_id": "ep-1"}]
    assert result.value == {"verified": "ep-1"}


def test_raw_input_survives_write_fence_and_fence_free_mid_graph_combine() -> None:
    from composable_agents.dag import Graph, StepKind, compile

    fenced = Graph()
    fenced.add_step(StepKind.TOOL, "read_episode", output="source", contract=READ_CONTRACT)
    fenced.add_step(
        StepKind.TOOL,
        "write_status",
        inputs=["source"],
        output="wrote",
        contract=WRITE_CONTRACT,
    )
    fenced.add_step(
        StepKind.PURE,
        "dag.combine_input_and_wrote",
        inputs=["__input__", "wrote"],
        output="result",
    )

    control = Graph()
    control.add_step(StepKind.TOOL, "read_episode", output="source", contract=READ_CONTRACT)
    control.add_step(StepKind.PURE, "dag.process_source", inputs=["source"], output="proc")
    control.add_step(
        StepKind.PURE,
        "dag.combine_input_and_proc",
        inputs=["__input__", "proc"],
        output="result",
    )

    def read_episode(value: dict[str, Any]) -> dict[str, Any]:
        return {"episode_id": value["episode_id"]}

    def write_status(value: dict[str, Any]) -> dict[str, Any]:
        return {"wrote": value["episode_id"]}

    env = InMemoryEnv(
        {},
        ProjectionEmitter(InMemoryProjection()),
        tools={"read_episode": read_episode, "write_status": write_status},
    )

    assert run(interpret(compile(fenced), {"episode_id": "ep-1"}, env)).value == {
        "input": "ep-1",
        "wrote": "ep-1",
    }
    assert run(interpret(compile(control), {"episode_id": "ep-2"}, env)).value == {
        "input": "ep-2",
        "proc": "ep-2",
    }


def test_liveness_keeps_raw_input_for_implicit_consumer_after_write() -> None:
    from composable_agents.dag import Graph, StepKind, compile

    graph = Graph()
    graph.add_step(StepKind.TOOL, "read_a", output="a", contract=READ_CONTRACT)
    graph.add_step(StepKind.TOOL, "read_b", output="b", contract=READ_CONTRACT)
    graph.add_step(
        StepKind.TOOL,
        "write_status",
        inputs=["a", "b"],
        output="wrote",
        contract=WRITE_CONTRACT,
    )
    graph.add_step(StepKind.TOOL, "verify_read", output="verified", contract=READ_CONTRACT)

    observed: list[dict[str, Any]] = []

    def read_a(value: dict[str, Any]) -> dict[str, Any]:
        return {"a": value["episode_id"]}

    def read_b(value: dict[str, Any]) -> dict[str, Any]:
        return {"b": value["episode_id"]}

    def write_status(value: dict[str, Any]) -> dict[str, Any]:
        return {"wrote": sorted(value)}

    def verify_read(value: dict[str, Any]) -> dict[str, Any]:
        observed.append(value)
        return {"verified": value["episode_id"]}

    env = InMemoryEnv(
        {},
        ProjectionEmitter(InMemoryProjection()),
        tools={
            "read_a": read_a,
            "read_b": read_b,
            "write_status": write_status,
            "verify_read": verify_read,
        },
    )

    result = run(interpret(compile(graph), {"episode_id": "ep-1"}, env))

    assert observed == [{"episode_id": "ep-1"}]
    assert result.value == {"verified": "ep-1"}


@pytest.mark.parametrize(
    ("found", "expected"),
    [
        (True, {"branch": "true", "episode_id": "ep-1"}),
        (False, {"branch": "false"}),
    ],
)
def test_cond_arm_with_no_declared_inputs_receives_raw_input(
    found: bool,
    expected: dict[str, Any],
) -> None:
    from composable_agents.dag import Graph, StepKind, compile

    then_arm = Graph(output_name="then_result")
    then_arm.add_step(
        StepKind.PURE,
        "dag.branch_true_from_source",
        inputs=["source"],
        output="then_result",
    )
    else_arm = Graph(output_name="else_result")
    else_arm.add_step(StepKind.PURE, "dag.branch_false_const", output="else_result")

    graph = Graph()
    graph.add_step(StepKind.TOOL, "read_episode", output="source", contract=READ_CONTRACT)
    graph.add_cond(
        "dag.is_found",
        inputs=["source"],
        output="result",
        if_true=then_arm,
        if_false=else_arm,
    )

    def read_episode(value: dict[str, Any]) -> dict[str, Any]:
        return {"episode_id": value["episode_id"], "found": found}

    env = InMemoryEnv(
        {},
        ProjectionEmitter(InMemoryProjection()),
        tools={"read_episode": read_episode},
    )

    assert run(interpret(compile(graph), {"episode_id": "ep-1"}, env)).value == expected


@pytest.mark.parametrize("found", [True, False])
def test_lone_cond_bootstraps_env_for_raw_input_arms(found: bool) -> None:
    from composable_agents.dag import Graph, StepKind, compile

    then_arm = Graph(output_name="then_result")
    then_arm.add_step(StepKind.PURE, "dag.branch_from_input", output="then_result")
    else_arm = Graph(output_name="else_result")
    else_arm.add_step(StepKind.PURE, "dag.branch_false_const", output="else_result")

    graph = Graph()
    graph.add_cond(
        "dag.input_flag",
        inputs=["__input__"],
        output="result",
        if_true=then_arm,
        if_false=else_arm,
    )

    result = run(
        interpret(
            compile(graph),
            {"episode_id": "ep-1", "found": found},
            InMemoryEnv({}, ProjectionEmitter(InMemoryProjection())),
        )
    )

    assert result.value == ({"branch": "ep-1"} if found else {"branch": "false"})


@pytest.mark.parametrize("found", [True, False])
def test_lone_cond_arms_can_declare_raw_input_edges(found: bool) -> None:
    from composable_agents.dag import Graph, StepKind, compile

    then_arm = Graph(output_name="then_result")
    then_arm.add_step(
        StepKind.PURE,
        "dag.branch_from_input",
        inputs=["__input__"],
        output="then_result",
    )
    else_arm = Graph(output_name="else_result")
    else_arm.add_step(
        StepKind.PURE,
        "dag.branch_from_input",
        inputs=["__input__"],
        output="else_result",
    )

    graph = Graph()
    graph.add_cond(
        "dag.input_flag",
        inputs=["__input__"],
        output="result",
        if_true=then_arm,
        if_false=else_arm,
    )

    result = run(
        interpret(
            compile(graph),
            {"episode_id": "ep-1", "found": found},
            InMemoryEnv({}, ProjectionEmitter(InMemoryProjection())),
        )
    )

    assert result.value == {"branch": "ep-1"}


def test_each_body_no_input_step_does_not_become_handle_capture() -> None:
    from composable_agents.dag import Graph, StepKind, compile

    body = Graph(input_name="item", output_name="copied")
    body.add_step(StepKind.PURE, "dag.branch_from_input", output="copied")

    graph = Graph()
    graph.add_step(StepKind.TOOL, "read_items", output="items", contract=READ_CONTRACT)
    graph.add_each(body, items="items", output="copied")

    def read_items(value: dict[str, Any]) -> list[dict[str, Any]]:
        return [{"episode_id": value["episode_id"]}, {"episode_id": "ep-2"}]

    compiled = compile(graph)
    assert all(node.pure != "std.each_pack" for node in compiled.walk())

    result = run(
        interpret(
            compiled,
            {"episode_id": "ep-1"},
            InMemoryEnv(
                {},
                ProjectionEmitter(InMemoryProjection()),
                tools={"read_items": read_items},
            ),
        )
    )

    assert result.value == [{"branch": "ep-1"}, {"branch": "ep-2"}]


def test_raw_input_is_pruned_after_last_consumer() -> None:
    from composable_agents.dag import Graph, StepKind, compile

    graph = Graph()
    graph.add_step(StepKind.TOOL, "read_episode", output="source", contract=READ_CONTRACT)
    graph.add_step(StepKind.PURE, "dag.input_identity", inputs=["__input__"], output="processed")
    graph.add_step(
        StepKind.TOOL,
        "write_status",
        inputs=["processed"],
        output="status",
        contract=WRITE_CONTRACT,
    )

    pack_args = [
        node.args
        for node in compile(graph).walk()
        if node.op is Op.ARR and node.pure == "std.pack"
    ]

    assert {"fields": {"processed": {"field": "processed"}}} not in pack_args
    assert {"fields": {"__input__": {"field": "__input__"}, "processed": {"field": "processed"}}} not in pack_args


def test_cond_branch_compiles_to_manual_alt_with_pruned_arm_envs() -> None:
    from composable_agents.dag import Graph, StepKind, compile

    then_arm = Graph(output_name="write_result")
    then_arm.add_step(
        StepKind.TOOL,
        "write_episode",
        inputs=["source"],
        output="write_result",
        contract=WRITE_CONTRACT,
    )
    else_arm = Graph(output_name="missing_result")
    else_arm.add_step(StepKind.PURE, "dag.missing_result", inputs=["source"], output="missing_result")

    graph = Graph()
    graph.add_step(StepKind.TOOL, "read_episode", output="source", contract=READ_CONTRACT)
    graph.add_cond(
        "dag.is_found",
        inputs=["source"],
        output="result",
        if_true=then_arm,
        if_false=else_arm,
    )

    compiled = compile(graph)
    expected = dsl.seq(
        dsl.call("read_episode"),
        dsl.arr("std.init", {"key": "source"}),
        dsl.arr("std.pack", {"fields": {"source": {"field": "source"}}}),
        dsl.alt(
            "dag.is_found",
            dsl.seq(
                dsl.arr("std.pluck", {"key": "source"}),
                dsl.call("write_episode"),
            ),
            dsl.seq(
                dsl.arr("std.pluck", {"key": "source"}),
                dsl.arr("dag.missing_result"),
            ),
        ),
    )

    arm_packs = [
        node.args
        for node in compiled.walk()
        if _is_std_arr(node, "std.pack", {"fields": {"source": {"field": "source"}}})
    ]
    assert len(arm_packs) == 1
    assert _canonical_ir(compiled) == _canonical_ir(expected)


def test_switch_branch_compiles_to_select_cases_alt() -> None:
    from composable_agents.dag import Graph, StepKind, compile

    def case_arm(pure_name: str, output: str) -> Graph:
        arm = Graph(output_name=output)
        arm.add_step(StepKind.PURE, pure_name, inputs=["status"], output=output)
        return arm

    graph = Graph()
    graph.add_step(StepKind.TOOL, "read_status", output="status", contract=READ_CONTRACT)
    graph.add_switch(
        "dag.status_selector",
        inputs=["status"],
        output="handled",
        cases={
            "success": case_arm("dag.case_success", "success_result"),
            "stale_source": case_arm("dag.case_stale", "stale_result"),
            "not_found": case_arm("dag.case_missing", "missing_result"),
        },
        default=case_arm("dag.case_default", "default_result"),
    )

    compiled = compile(graph)
    expected = dsl.seq(
        dsl.call("read_status"),
        dsl.arr("std.init", {"key": "status"}),
        dsl.arr("std.pack", {"fields": {"status": {"field": "status"}}}),
        dsl.alt(
            select="dag.status_selector",
            cases={
                "success": dsl.seq(
                    dsl.arr("std.pluck", {"key": "status"}),
                    dsl.arr("dag.case_success"),
                ),
                "stale_source": dsl.seq(
                    dsl.arr("std.pluck", {"key": "status"}),
                    dsl.arr("dag.case_stale"),
                ),
                "not_found": dsl.seq(
                    dsl.arr("std.pluck", {"key": "status"}),
                    dsl.arr("dag.case_missing"),
                ),
            },
            default=dsl.seq(
                dsl.arr("std.pluck", {"key": "status"}),
                dsl.arr("dag.case_default"),
            ),
        ),
    )

    assert _canonical_ir(compiled) == _canonical_ir(expected)


def test_mid_flow_cond_result_feeds_later_step_and_prunes_source() -> None:
    from composable_agents.dag import Graph, StepKind, compile

    then_arm = Graph(output_name="write_result")
    then_arm.add_step(
        StepKind.TOOL,
        "write_episode",
        inputs=["source"],
        output="write_result",
        contract=WRITE_CONTRACT,
    )
    else_arm = Graph(output_name="missing_result")
    else_arm.add_step(StepKind.PURE, "dag.missing_result", inputs=["source"], output="missing_result")

    graph = Graph()
    graph.add_step(StepKind.TOOL, "read_episode", output="source", contract=READ_CONTRACT)
    graph.add_cond(
        "dag.is_found",
        inputs=["source"],
        output="decision",
        if_true=then_arm,
        if_false=else_arm,
    )
    graph.add_step(StepKind.PURE, "dag.decorate_decision", inputs=["decision"], output="decorated")

    compiled = compile(graph)
    expected = dsl.seq(
        dsl.call("read_episode"),
        dsl.arr("std.init", {"key": "source"}),
        dsl.par(
            dsl.ident(),
            dsl.seq(
                dsl.arr("std.pack", {"fields": {"source": {"field": "source"}}}),
                dsl.alt(
                    "dag.is_found",
                    dsl.seq(
                        dsl.arr("std.pluck", {"key": "source"}),
                        dsl.call("write_episode"),
                    ),
                    dsl.seq(
                        dsl.arr("std.pluck", {"key": "source"}),
                        dsl.arr("dag.missing_result"),
                    ),
                ),
            ),
        ),
        dsl.arr("std.assign", {"key": "decision"}),
        dsl.arr("std.pluck", {"key": "decision"}),
        dsl.arr("dag.decorate_decision"),
    )

    assert _canonical_ir(compiled) == _canonical_ir(expected)


def test_two_branches_in_one_flow_have_unique_deterministic_outputs() -> None:
    from composable_agents.dag import Graph, StepKind, compile

    def missing_arm(output: str) -> Graph:
        arm = Graph(output_name=output)
        arm.add_step(StepKind.PURE, "dag.missing_result", inputs=["source"], output=output)
        return arm

    graph = Graph(output_name="decorated")
    graph.add_step(StepKind.TOOL, "read_episode", output="source", contract=READ_CONTRACT)
    graph.add_cond(
        "dag.is_found",
        inputs=["source"],
        output="first",
        if_true=missing_arm("first_true"),
        if_false=missing_arm("first_false"),
    )
    graph.add_cond(
        "dag.is_found",
        inputs=["source", "first"],
        output="second",
        if_true=missing_arm("second_true"),
        if_false=missing_arm("second_false"),
    )
    graph.add_step(StepKind.PURE, "dag.decorate_decision", inputs=["second"], output="decorated")

    compiled = compile(graph)
    alt_ids = [node.id for node in compiled.walk() if node.op is Op.ALT]
    assert len(alt_ids) == 2
    assert len(set(alt_ids)) == 2
    assert '"key":"first"' in _canonical_ir(compiled)
    assert '"key":"second"' in _canonical_ir(compiled)


def test_return_any_handle_projects_that_value_not_whole_env() -> None:
    from composable_agents.dag import Graph, StepKind, compile

    graph = Graph(output_name="summary")
    graph.add_step(StepKind.TOOL, "read_episode", output="source", contract=READ_CONTRACT)
    graph.add_step(StepKind.THINK, "summarizer", inputs=["source"], output="summary")
    graph.add_step(
        StepKind.TOOL,
        "write_summary",
        inputs=["summary"],
        output="status",
        contract=WRITE_CONTRACT,
    )

    def read_episode(value: dict[str, Any]) -> dict[str, Any]:
        return {"episode_id": value["episode_id"], "text": "Ada met Ben."}

    def summarizer(value: dict[str, Any]) -> dict[str, Any]:
        return {"summary": value["text"]}

    def write_summary(value: dict[str, Any]) -> dict[str, Any]:
        return {"status": "success", "summary": value["summary"]}

    env = InMemoryEnv(
        {},
        ProjectionEmitter(InMemoryProjection()),
        tools={"read_episode": read_episode, "write_summary": write_summary},
        reasoners={"summarizer": summarizer},
    )

    result = run(interpret(compile(graph), {"episode_id": "ep-1"}, env))

    assert result.value == {"summary": "Ada met Ben."}


@pytest.mark.parametrize(
    ("found", "expected"),
    [
        (True, {"status": "success", "episode_id": "ep-1"}),
        (False, {"status": "not_found", "episode_id": "ep-1"}),
    ],
)
def test_compiled_cond_runs_every_arm(found: bool, expected: dict[str, Any]) -> None:
    from composable_agents.dag import Graph, StepKind, compile

    then_arm = Graph(output_name="write_result")
    then_arm.add_step(
        StepKind.TOOL,
        "write_episode",
        inputs=["source"],
        output="write_result",
        contract=WRITE_CONTRACT,
    )
    else_arm = Graph(output_name="missing_result")
    else_arm.add_step(StepKind.PURE, "dag.missing_result", inputs=["source"], output="missing_result")

    graph = Graph()
    graph.add_step(StepKind.TOOL, "read_episode", output="source", contract=READ_CONTRACT)
    graph.add_cond(
        "dag.is_found",
        inputs=["source"],
        output="result",
        if_true=then_arm,
        if_false=else_arm,
    )

    def read_episode(value: dict[str, Any]) -> dict[str, Any]:
        return {"episode_id": value["episode_id"], "found": found}

    def write_episode(value: dict[str, Any]) -> dict[str, Any]:
        return {"status": "success", "episode_id": value["episode_id"]}

    env = InMemoryEnv(
        {},
        ProjectionEmitter(InMemoryProjection()),
        tools={"read_episode": read_episode, "write_episode": write_episode},
    )

    result = run(interpret(compile(graph), {"episode_id": "ep-1"}, env))

    assert result.value == expected


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        ("success", "success"),
        ("stale_source", "stale"),
        ("not_found", "missing"),
        ("rate_limited", "default"),
    ],
)
def test_compiled_switch_runs_every_case_and_default(status: str, expected: str) -> None:
    from composable_agents.dag import Graph, StepKind, compile

    def case_arm(pure_name: str, output: str) -> Graph:
        arm = Graph(output_name=output)
        arm.add_step(StepKind.PURE, pure_name, inputs=["status"], output=output)
        return arm

    graph = Graph()
    graph.add_step(StepKind.TOOL, "read_status", output="status", contract=READ_CONTRACT)
    graph.add_switch(
        "dag.status_selector",
        inputs=["status"],
        output="handled",
        cases={
            "success": case_arm("dag.case_success", "success_result"),
            "stale_source": case_arm("dag.case_stale", "stale_result"),
            "not_found": case_arm("dag.case_missing", "missing_result"),
        },
        default=case_arm("dag.case_default", "default_result"),
    )

    def read_status(value: dict[str, Any]) -> dict[str, Any]:
        return {"status": status, "episode_id": value["episode_id"]}

    env = InMemoryEnv(
        {},
        ProjectionEmitter(InMemoryProjection()),
        tools={"read_status": read_status},
    )

    result = run(interpret(compile(graph), {"episode_id": "ep-1"}, env))

    assert result.value == {"handled": expected, "episode_id": "ep-1"}


def test_branch_arm_liveness_prunes_fields_per_arm() -> None:
    from composable_agents.dag import Graph, StepKind, compile

    then_arm = Graph(output_name="then_result")
    then_arm.add_step(StepKind.PURE, "dag.case_success", inputs=["status"], output="then_result")
    else_arm = Graph(output_name="else_result")
    else_arm.add_step(StepKind.PURE, "dag.missing_result", inputs=["source"], output="else_result")

    graph = Graph()
    graph.add_step(StepKind.TOOL, "read_episode", output="source", contract=READ_CONTRACT)
    graph.add_step(StepKind.TOOL, "read_status", output="status", contract=READ_CONTRACT)
    graph.add_cond(
        "dag.is_found",
        inputs=["source"],
        output="result",
        if_true=then_arm,
        if_false=else_arm,
    )

    compiled = compile(graph)
    pack_args = [
        node.args
        for node in compiled.walk()
        if node.op is Op.ARR and node.pure == "std.pack"
    ]

    assert {"fields": {"source": {"field": "source"}, "status": {"field": "status"}}} in pack_args
    assert {"fields": {"status": {"field": "status"}}} not in pack_args
    assert {"fields": {"source": {"field": "source"}}} not in pack_args


def test_each_with_handle_capture_compiles_to_pre_each_env_projection() -> None:
    from composable_agents.dag import Graph, StepKind, compile

    body = Graph(input_name="cluster", output_name="label")
    body.add_step(
        StepKind.PURE,
        "dag.make_cluster_label",
        inputs=["store_context", "cluster"],
        output="label",
    )

    graph = Graph()
    graph.add_step(StepKind.TOOL, "read_store_context", output="store_context", contract=READ_CONTRACT)
    graph.add_step(
        StepKind.TOOL,
        "read_clusters",
        inputs=["store_context"],
        output="clusters",
        contract=READ_CONTRACT,
    )
    graph.add_each(
        body,
        items="clusters",
        output="labels",
        max_parallel=3,
    )

    compiled = compile(graph)
    expected = dsl.seq(
        dsl.call("read_store_context"),
        dsl.arr("std.init", {"key": "store_context"}),
        dsl.par(
            dsl.ident(),
            dsl.seq(dsl.arr("std.pluck", {"key": "store_context"}), dsl.call("read_clusters")),
        ),
        dsl.arr("std.assign", {"key": "clusters"}),
        dsl.arr(
            "std.each_pack",
            {
                "items": "clusters",
                "item": "cluster",
                "fields": {"store_context": "store_context"},
                "consts": {},
            },
        ),
        dsl.each(
            dsl.seq(
                dsl.arr(
                    "std.unpack",
                    {"fields": {"cluster": "cluster", "store_context": "store_context"}},
                ),
                dsl.arr("std.merge", {"fields": ["store_context", "cluster"]}),
                dsl.arr("dag.make_cluster_label"),
            ),
            max_parallel=3,
        ),
    )

    each_pack_nodes = [
        node for node in compiled.walk() if node.op is Op.ARR and node.pure == "std.each_pack"
    ]
    assert len(each_pack_nodes) == 1
    assert _canonical_ir(compiled) == _canonical_ir(expected)


def test_each_that_captures_its_items_source_uses_env_path() -> None:
    from composable_agents.dag import Graph, StepKind, compile

    body = Graph(input_name="cluster", output_name="labeled")
    body.add_step(
        StepKind.PURE,
        "dag.cluster_count",
        inputs=["clusters"],
        output="cluster_count",
    )
    body.add_step(
        StepKind.PURE,
        "std.merge",
        inputs=["cluster", "cluster_count"],
        output="labeled",
    )

    graph = Graph()
    graph.add_step(StepKind.TOOL, "read_clusters", output="clusters", contract=READ_CONTRACT)
    graph.add_each(body, items="clusters", output="labels")

    compiled = compile(graph)
    each_pack_nodes = [
        node for node in compiled.walk() if node.op is Op.ARR and node.pure == "std.each_pack"
    ]
    assert [node.args for node in each_pack_nodes] == [
        {
            "items": "clusters",
            "item": "cluster",
            "fields": {"clusters": "clusters"},
            "consts": {},
        }
    ]

    def read_clusters(value: dict[str, Any]) -> list[dict[str, Any]]:
        return [{"cluster_id": value["first"]}, {"cluster_id": "c2"}]

    env = InMemoryEnv(
        {},
        ProjectionEmitter(InMemoryProjection()),
        tools={"read_clusters": read_clusters},
    )

    result = run(interpret(compiled, {"first": "c1"}, env))

    assert result.value == [
        {"cluster_id": "c1", "cluster_count": 2},
        {"cluster_id": "c2", "cluster_count": 2},
    ]


def test_each_with_const_captures_only_pins_consts_in_body_pack() -> None:
    from composable_agents.dag import Graph, StepKind, compile

    body = Graph(input_name="cluster", output_name="labeled")
    body.add_step(
        StepKind.PURE,
        "dag.attach_const_model",
        inputs=["cluster", "model_config"],
        output="labeled",
    )

    graph = Graph()
    graph.add_step(StepKind.TOOL, "read_clusters", output="clusters", contract=READ_CONTRACT)
    graph.add_each(
        body,
        items="clusters",
        output="labels",
        const_captures={"model_config": {"model": "mini"}},
    )

    expected = dsl.seq(
        dsl.call("read_clusters"),
        dsl.each(
            dsl.seq(
                dsl.arr(
                    "std.pack",
                    {
                        "fields": {
                            "cluster": {"input": True},
                            "model_config": {"const": {"model": "mini"}},
                        }
                    },
                ),
                dsl.arr(
                    "std.unpack",
                    {"fields": {"cluster": "cluster", "model_config": "model_config"}},
                ),
                dsl.arr("std.merge", {"fields": ["cluster", "model_config"]}),
                dsl.arr("dag.attach_const_model"),
            )
        ),
    )

    assert _canonical_ir(compile(graph)) == _canonical_ir(expected)


def test_each_with_reducer_lowers_to_dsl_each_reducer() -> None:
    from composable_agents.dag import Graph, StepKind, compile

    body = Graph(input_name="cluster", output_name="labeled")
    body.add_step(
        StepKind.PURE,
        "dag.attach_const_model",
        inputs=["cluster", "model_config"],
        output="labeled",
    )

    graph = Graph()
    graph.add_step(StepKind.TOOL, "read_clusters", output="clusters", contract=READ_CONTRACT)
    graph.add_each(
        body,
        items="clusters",
        output="labels",
        const_captures={"model_config": {"model": "mini"}},
        reducer="dag.tally_cluster_statuses",
        max_parallel=2,
    )

    compiled = compile(graph)
    each_nodes = [node for node in compiled.walk() if node.op is Op.EACH]
    assert len(each_nodes) == 1
    assert each_nodes[0].pure == "dag.tally_cluster_statuses"
    assert each_nodes[0].bound == 2


@pytest.mark.parametrize(
    ("stale", "expected"),
    [
        (False, {"success": 2, "stale": 0}),
        (True, {"success": 1, "stale": 1}),
    ],
)
def test_cluster_labeling_skeleton_each_runs_success_and_stale(
    stale: bool,
    expected: dict[str, int],
) -> None:
    from composable_agents.dag import Graph, StepKind, compile

    body = Graph(input_name="cluster", output_name="write_status")
    body.add_step(
        StepKind.PURE,
        "dag.make_cluster_label",
        inputs=["store_context", "cluster"],
        output="label",
    )
    body.add_step(
        StepKind.TOOL,
        "write_cluster_label",
        inputs=["label"],
        output="write_status",
        contract=WRITE_CONTRACT,
    )

    graph = Graph()
    graph.add_step(StepKind.TOOL, "read_store_context", output="store_context", contract=READ_CONTRACT)
    graph.add_step(
        StepKind.TOOL,
        "read_clusters",
        inputs=["store_context"],
        output="clusters",
        contract=READ_CONTRACT,
    )
    graph.add_each(
        body,
        items="clusters",
        output="statuses",
        max_parallel=2,
        reducer="dag.tally_cluster_statuses",
    )

    def read_store_context(value: dict[str, Any]) -> dict[str, Any]:
        return {
            "store_id": value["store_id"],
            "prefix": "topic",
            "revision": 7,
        }

    def read_clusters(value: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            {"store_id": value["store_id"], "cluster_id": "c1"},
            {"store_id": value["store_id"], "cluster_id": "c2"},
        ]

    def write_cluster_label(value: dict[str, Any]) -> dict[str, Any]:
        if stale and value["cluster_id"] == "c2":
            return {"status": "stale_source", "cluster_id": value["cluster_id"]}
        return {"status": "success", "cluster_id": value["cluster_id"]}

    env = InMemoryEnv(
        {},
        ProjectionEmitter(InMemoryProjection()),
        tools={
            "read_store_context": read_store_context,
            "read_clusters": read_clusters,
            "write_cluster_label": write_cluster_label,
        },
    )

    result = run(interpret(compile(graph), {"store_id": "s1"}, env))

    assert result.value == expected


def test_each_capture_policy_rejects_foreign_body_handles_and_non_json_consts() -> None:
    from composable_agents.dag import Graph, GraphDefinitionError, StepKind

    body = Graph(input_name="cluster")
    body.add_step(StepKind.PURE, "std.merge", inputs=["cluster", "missing_context"], output="label")

    graph = Graph()
    graph.add_step(StepKind.TOOL, "read_clusters", output="clusters", contract=READ_CONTRACT)
    with pytest.raises(GraphDefinitionError, match="foreign-scope handle capture: missing_context"):
        graph.add_each(body, items="clusters", output="labels")

    with pytest.raises(GraphDefinitionError, match="const capture .* JSON"):
        graph.add_each(body, items="clusters", output="labels", const_captures={"missing_context": object()})


def test_each_const_capture_warns_only_when_canonical_json_exceeds_threshold() -> None:
    from composable_agents.dag import CAPTURE_SIZE_WARNING_BYTES, Graph, StepKind

    def build_graph_with_capture(capture: dict[str, Any]) -> None:
        body = Graph(input_name="cluster", output_name="labeled")
        body.add_step(
            StepKind.PURE,
            "dag.attach_const_model",
            inputs=["cluster", "model_config"],
            output="labeled",
        )
        graph = Graph()
        graph.add_step(StepKind.TOOL, "read_clusters", output="clusters", contract=READ_CONTRACT)
        graph.add_each(
            body,
            items="clusters",
            output="labels",
            const_captures={"model_config": capture},
        )

    oversized_capture = {"payload": "x" * CAPTURE_SIZE_WARNING_BYTES}
    warning_match = rf"const capture 'model_config'.*{CAPTURE_SIZE_WARNING_BYTES} bytes"
    with pytest.warns(UserWarning, match=warning_match):
        build_graph_with_capture(oversized_capture)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        build_graph_with_capture({"payload": "small"})

    assert caught == []


def test_source_spans_propagate_to_each_and_shims_without_wire_bytes() -> None:
    from composable_agents.dag import Graph, StepKind, compile

    parent_span = SourceSpan("flow.py", 10, "build", "labels = each(...)")
    body_span = SourceSpan("flow.py", 6, "label_one", "label = make(...)")

    body = Graph(input_name="cluster", output_name="label")
    body.add_step(
        StepKind.PURE,
        "dag.attach_const_model",
        inputs=["cluster", "model_config"],
        output="label",
        source=body_span,
    )

    graph = Graph()
    graph.add_step(
        StepKind.TOOL,
        "read_clusters",
        output="clusters",
        contract=READ_CONTRACT,
        source=parent_span,
    )
    graph.add_each(
        body,
        items="clusters",
        output="labels",
        const_captures={"model_config": {"model": "mini"}},
        source=parent_span,
    )

    compiled = compile(graph)

    assert all(node.source is not None for node in compiled.walk())
    assert any(
        node.op is Op.ARR and node.pure == "std.pack" and node.source == parent_span
        for node in compiled.walk()
    )
    assert any(
        node.op is Op.ARR and node.pure == "dag.attach_const_model" and node.source == body_span
        for node in compiled.walk()
    )
    assert "source" not in canonical_json(compiled.to_json())
