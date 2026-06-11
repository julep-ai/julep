from __future__ import annotations

from typing import Any

import pytest

from composable_agents import dsl
from composable_agents.contracts import ToolContract
from composable_agents.execution.interpreter import InMemoryEnv, interpret
from composable_agents.ir import Node, canonical_json
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


READ_CONTRACT = ToolContract(effect=Effect.READ, idempotency=Idempotency.NATIVE)
WRITE_CONTRACT = ToolContract(effect=Effect.WRITE, idempotency=Idempotency.NONE)


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
        hands={"read_episode": read_episode, "write_summary": write_summary},
        brains={"summarizer": summarizer, "embedder": embedder},
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
