from __future__ import annotations

from typing import Any

import pytest

from composable_agents import dsl, pure
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
        dsl.arr("std.pack", {"fields": {"source": {"field": "source"}}}),
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


def test_cond_branch_compiles_to_hand_written_alt_with_pruned_arm_envs() -> None:
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
                dsl.arr("std.pack", {"fields": {"source": {"field": "source"}}}),
                dsl.arr("std.pluck", {"key": "source"}),
                dsl.call("write_episode"),
            ),
            dsl.seq(
                dsl.arr("std.pack", {"fields": {"source": {"field": "source"}}}),
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
    assert len(arm_packs) == 3
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
                    dsl.arr("std.pack", {"fields": {"status": {"field": "status"}}}),
                    dsl.arr("std.pluck", {"key": "status"}),
                    dsl.arr("dag.case_success"),
                ),
                "stale_source": dsl.seq(
                    dsl.arr("std.pack", {"fields": {"status": {"field": "status"}}}),
                    dsl.arr("std.pluck", {"key": "status"}),
                    dsl.arr("dag.case_stale"),
                ),
                "not_found": dsl.seq(
                    dsl.arr("std.pack", {"fields": {"status": {"field": "status"}}}),
                    dsl.arr("std.pluck", {"key": "status"}),
                    dsl.arr("dag.case_missing"),
                ),
            },
            default=dsl.seq(
                dsl.arr("std.pack", {"fields": {"status": {"field": "status"}}}),
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
                        dsl.arr("std.pack", {"fields": {"source": {"field": "source"}}}),
                        dsl.arr("std.pluck", {"key": "source"}),
                        dsl.call("write_episode"),
                    ),
                    dsl.seq(
                        dsl.arr("std.pack", {"fields": {"source": {"field": "source"}}}),
                        dsl.arr("std.pluck", {"key": "source"}),
                        dsl.arr("dag.missing_result"),
                    ),
                ),
            ),
        ),
        dsl.arr("std.assign", {"key": "decision"}),
        dsl.arr("std.pack", {"fields": {"decision": {"field": "decision"}}}),
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
        hands={"read_episode": read_episode, "write_summary": write_summary},
        brains={"summarizer": summarizer},
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
        hands={"read_episode": read_episode, "write_episode": write_episode},
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
        hands={"read_status": read_status},
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
    assert {"fields": {"status": {"field": "status"}}} in pack_args
    assert {"fields": {"source": {"field": "source"}}} in pack_args
