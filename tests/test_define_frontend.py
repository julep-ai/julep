from __future__ import annotations

from typing import Any

import pytest

from composable_agents import as_flow, deploy, dsl, flow, pure, think, tool
from composable_agents.define import DefineError, Handle
from composable_agents.ir import Node, ThinkStep, canonical_json
from composable_agents.kinds import Op
from composable_agents.transforms import normalize_ids


def _canonical_ir(node: Node) -> str:
    return canonical_json(normalize_ids(Node.from_json(node.to_json())).to_json())


@tool(effect="read", idempotent=True)
def p51_read_episode(episode_id: str) -> dict[str, Any]:
    return {"episode_id": episode_id, "body": "hello"}


@tool(effect="write")
def p51_write_summary(payload: dict[str, Any]) -> dict[str, Any]:
    return {"status": "success", "episode_id": payload["episode_id"]}


@tool(effect="read", idempotent=True)
def p51_echo_with_limit(payload: dict[str, Any]) -> dict[str, Any]:
    copied = dict(payload)
    return copied


@pure("p51.identity")
def p51_identity(value: dict[str, Any]) -> dict[str, Any]:
    return dict(value)


@pure("p51.inner")
def p51_inner(value: dict[str, Any]) -> dict[str, Any]:
    return {**value, "inner": True}


@pure("p51.outer")
def p51_outer(value: dict[str, Any]) -> dict[str, Any]:
    return {**value, "outer": True}


def test_think_string_form_still_emits_dsl_think_directly() -> None:
    assert _canonical_ir(think("p51.brain")) == _canonical_ir(dsl.think("p51.brain"))


def test_flow_decorator_calls_body_once_and_builds_graph() -> None:
    calls = 0

    @flow
    def happy_path(source: dict[str, Any]) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        summary = think("p51.summarizer", source)
        merged = source | summary
        liner = think("p51.one_liner", merged)
        payload = merged | liner
        status = p51_write_summary(payload)
        return status

    assert calls == 1

    from composable_agents.dag import Graph, StepKind, compile

    graph = Graph(input_name="source")
    graph.add_step(StepKind.THINK, "p51.summarizer", output="summary")
    graph.add_step(StepKind.PURE, "std.merge", inputs=["source", "summary"], output="merged")
    graph.add_step(StepKind.THINK, "p51.one_liner", inputs=["merged"], output="liner")
    graph.add_step(StepKind.PURE, "std.merge", inputs=["merged", "liner"], output="payload")
    graph.add_step(
        StepKind.TOOL,
        p51_write_summary.name,
        inputs=["payload"],
        output="status",
        contract=p51_write_summary.contract,
    )

    assert _canonical_ir(happy_path.to_ir()) == _canonical_ir(compile(graph))


def test_two_think_steps_from_same_handle_compile_into_one_par_layer() -> None:
    @flow
    def summarize_and_embed(source: dict[str, Any]) -> dict[str, Any]:
        summary = think("p51.summary", source)
        embedding = think("p51.embedding", source)
        payload = source | summary | embedding
        status = p51_write_summary(payload)
        return status

    par_layers = [node for node in summarize_and_embed.to_ir().walk() if node.op is Op.PAR]
    assert any(
        {
            child.step.brain
            for child in layer.walk()
            if isinstance(child.step, ThinkStep)
        }
        == {"p51.summary", "p51.embedding"}
        for layer in par_layers
    )


def test_in_flow_subflow_application_inlines_to_same_ir_as_inline_steps() -> None:
    @flow
    def sub(source: dict[str, Any]) -> dict[str, Any]:
        enriched = p51_inner(source)
        out = p51_outer(enriched)
        return out

    @flow
    def parent(source: dict[str, Any]) -> dict[str, Any]:
        y = sub(source)
        return y

    @flow
    def inline(source: dict[str, Any]) -> dict[str, Any]:
        enriched = p51_inner(source)
        y = p51_outer(enriched)
        return y

    assert _canonical_ir(parent.to_ir()) == _canonical_ir(inline.to_ir())


def test_in_flow_subflow_application_preserves_multi_step_body() -> None:
    @flow
    def sub(source: dict[str, Any]) -> dict[str, Any]:
        inner = p51_inner(source)
        outer = p51_outer(inner)
        return outer

    @flow
    def parent(source: dict[str, Any]) -> dict[str, Any]:
        y = sub(source)
        return y

    pure_names = [node.pure for node in parent.to_ir().walk() if node.pure is not None]
    assert "p51.inner" in pure_names
    assert "p51.outer" in pure_names


def test_flow_returning_raw_input_after_steps_is_rejected() -> None:
    with pytest.raises(
        DefineError,
        match=r"returns its own input 'source' after authoring steps.*return a step output handle",
    ):

        @flow
        def writes_then_returns_input(source: dict[str, Any]) -> dict[str, Any]:
            _status = p51_write_summary(source)
            return source


def test_in_flow_multi_param_subflow_single_handle_raises_define_error() -> None:
    @flow
    def two_params(source: dict[str, Any], limit: dict[str, Any]) -> dict[str, Any]:
        merged = source | limit
        out = p51_inner(merged)
        return out

    with pytest.raises(
        DefineError,
        match=r"@flow subcall 'two_params' currently needs exactly one Handle argument",
    ):

        @flow
        def parent(source: dict[str, Any]) -> dict[str, Any]:
            y = two_params(source)
            return y


def test_chained_merge_assignment_name_lands_on_outermost_merge() -> None:
    @flow
    def chained(source: dict[str, Any]) -> dict[str, Any]:
        b = p51_inner(source)
        c = p51_outer(source)
        payload = source | b | c
        return payload

    merges = [step for step in chained.graph.steps if step.ref == "std.merge"]

    assert len(merges) == 2
    assert merges[0].output != "payload"
    assert merges[-1].output == "payload"
    assert [edge.source for edge in merges[-1].inputs] == [merges[0].output, "c"]


def test_nested_call_assignment_name_lands_on_outermost_call() -> None:
    @flow
    def nested(source: dict[str, Any]) -> dict[str, Any]:
        result = p51_outer(p51_inner(source))
        return result

    inner_step = next(step for step in nested.graph.steps if step.ref == "p51.inner")
    outer_step = next(step for step in nested.graph.steps if step.ref == "p51.outer")

    assert inner_step.output != "result"
    assert outer_step.output == "result"
    assert [edge.source for edge in outer_step.inputs] == [inner_step.output]


def test_read_then_write_keeps_authored_order() -> None:
    @flow
    def read_then_write(episode_id: str) -> dict[str, Any]:
        source = p51_read_episode(episode_id)
        status = p51_write_summary(source)
        return status

    expected = dsl.seq(
        dsl.call(p51_read_episode.name),
        dsl.call(p51_write_summary.name),
    )

    assert _canonical_ir(read_then_write.to_ir()) == _canonical_ir(expected)


def test_tool_kwargs_lower_to_std_bind_before_call() -> None:
    @flow
    def bind_limit(source: dict[str, Any]) -> dict[str, Any]:
        limited = p51_echo_with_limit(source, limit=5)
        return limited

    expected = dsl.seq(
        dsl.arr("std.bind", {"consts": {"limit": 5}}),
        dsl.call(p51_echo_with_limit.name),
    )

    assert _canonical_ir(bind_limit.to_ir()) == _canonical_ir(expected)


def test_linear_authored_flow_dry_run_matches_combinator_flow() -> None:
    @flow
    def linear(episode_id: str) -> dict[str, Any]:
        source = p51_read_episode(episode_id)
        status = p51_write_summary(source)
        return status

    authored = deploy(linear, tools=[p51_read_episode, p51_write_summary])
    combinator = deploy(
        as_flow(dsl.seq(dsl.call(p51_read_episode.name), dsl.call(p51_write_summary.name))),
        tools=[p51_read_episode, p51_write_summary],
    )

    assert authored.dry_run("ep-1").value == combinator.dry_run("ep-1").value


def test_handle_bool_iter_and_attribute_errors_are_actionable() -> None:
    handle = Handle.synthetic("source")
    with pytest.raises(TypeError, match=r"Handle truthiness.*cond\(.*<synthetic>:1"):
        bool(handle)
    with pytest.raises(TypeError, match=r"Handle iteration.*each\(.*<synthetic>:1"):
        iter(handle)
    with pytest.raises(AttributeError, match=r"Handle attribute access.*source.foo.*Use source\['foo'\]"):
        attr = "foo"
        getattr(handle, attr)
    assert not hasattr(handle, "foo")


def test_unregistered_plain_function_on_handle_names_location_and_hint() -> None:
    def plain(value: object) -> object:
        return value

    with pytest.raises(DefineError, match=r"unregistered callable 'plain'.*test_define_frontend.py:"):

        @flow
        def bad(source: dict[str, Any]) -> object:
            value = plain(source)
            return value


def test_rebinding_step_output_names_location_and_hint() -> None:
    with pytest.raises(DefineError, match=r"step output name 'source' is already bound.*choose a new Python variable name"):

        @flow
        def bad(source: dict[str, Any]) -> dict[str, Any]:
            source = p51_identity(source)
            return source


def test_public_flow_name_is_decorator_and_as_flow_is_lift() -> None:
    @flow
    def identity(value: dict[str, Any]) -> dict[str, Any]:
        copied = p51_identity(value)
        return copied

    assert _canonical_ir(identity.to_ir()) == _canonical_ir(dsl.arr("p51.identity"))
    assert _canonical_ir(as_flow(dsl.ident()).to_ir()) == _canonical_ir(dsl.ident())


def test_tool_application_per_call_options_attach_ann() -> None:
    @flow
    def with_options(episode_id: str) -> dict[str, Any]:
        source = p51_read_episode(
            episode_id,
            retries=3,
            retry_interval_s=0.5,
            backoff_rate=2.0,
            timeout_s=10,
        )
        return source

    prims = [node for node in with_options.to_ir().walk() if node.step is not None]
    assert len(prims) == 1
    assert prims[0].ann is not None
    assert prims[0].ann.to_json() == {
        "timeout": 10,
        "maxAttempts": 3,
        "retryIntervalS": 0.5,
        "backoffRate": 2.0,
    }


def test_bound_flow_with_one_runtime_argument_is_flowlike() -> None:
    @flow
    def bounded(source: dict[str, Any], limit: dict[str, Any]) -> dict[str, Any]:
        merged = source | limit
        limited = p51_echo_with_limit(merged)
        return limited

    applied = bounded(limit={"limit": 7})
    deployment = deploy(applied, tools=[p51_echo_with_limit])

    assert deployment.dry_run({"episode_id": "ep-1"}).value == {
        "episode_id": "ep-1",
        "limit": 7,
    }
