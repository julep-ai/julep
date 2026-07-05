from __future__ import annotations

from typing import Any

import pytest

import julep as ca
from julep import as_flow, cond, delay, deploy, dsl, each, flow, pure, reschedule, switch, think, tool
from julep.define import DefineError, Handle
from julep.ir import Node, SLEEP_TOOL, CallStep, NativeTool, ThinkStep, canonical_json
from julep.kinds import Op
from julep.validate import SECRET_KEY_RE
from julep.transforms import normalize_ids


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


@pure("p6fix.scale")
def p6fix_scale(value: dict[str, Any], factor: int = 1) -> dict[str, Any]:
    return {"scaled": value["n"] * factor}


@pure("p6fix.affix")
def p6fix_affix(value: str, prefix: str = "", suffix: str = "") -> str:
    return f"{prefix}{value}{suffix}"


@pure("p6fix.scale_offset")
def p6fix_scale_offset(value: dict[str, Any], factor: int = 1, offset: int = 0) -> dict[str, Any]:
    return {"scaled": value["n"] * factor + offset}


@tool(effect="write")
def p52_write_cas(payload: dict[str, Any]) -> dict[str, Any]:
    return {"status": payload["status"], "episode_id": payload["episode_id"]}


@tool(effect="write")
def p52_mark_dirty(payload: dict[str, Any]) -> dict[str, Any]:
    return dict(payload)


@pure("p52.episode_found")
def p52_episode_found(source: dict[str, Any]) -> bool:
    return bool(source["found"])


@pure("p52.cas_status")
def p52_cas_status(write_result: dict[str, Any]) -> str:
    return str(write_result["status"])


@pure("p52.case_success")
def p52_case_success(write_result: dict[str, Any]) -> dict[str, Any]:
    return {"handled": "success", "episode_id": write_result["episode_id"]}


@pure("p52.case_stale")
def p52_case_stale(write_result: dict[str, Any]) -> dict[str, Any]:
    return {"handled": "stale", "episode_id": write_result["episode_id"]}


@pure("p52.case_missing")
def p52_case_missing(write_result: dict[str, Any]) -> dict[str, Any]:
    return {"handled": "missing", "episode_id": write_result["episode_id"]}


@pure("p52.case_default")
def p52_case_default(write_result: dict[str, Any]) -> dict[str, Any]:
    return {"handled": "default", "episode_id": write_result["episode_id"]}


@pure("p52.make_cluster_label")
def p52_make_cluster_label(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "store_id": payload["store_id"],
        "cluster_id": payload["cluster_id"],
        "label": f"{payload['store_id']}:{payload['cluster_id']}",
    }


@pure("p52.tally_cluster_labels")
def p52_tally_cluster_labels(labels: list[dict[str, Any]]) -> dict[str, Any]:
    return {"count": len(labels), "ids": [label["cluster_id"] for label in labels]}


@pure("p5fix.parent_ctx")
def p5fix_parent_ctx(_source: dict[str, Any]) -> dict[str, Any]:
    return {"ctx": "parent-ctx"}


@pure("p5fix.child_ctx")
def p5fix_child_ctx(_source: dict[str, Any]) -> dict[str, Any]:
    return {"ctx": "child-ctx"}


@pure("p5fix.parent_subject")
def p5fix_parent_subject(_source: dict[str, Any]) -> dict[str, Any]:
    return {"subject": "parent-subject", "ok": True, "case": "hit"}


@pure("p5fix.child_subject")
def p5fix_child_subject(_source: dict[str, Any]) -> dict[str, Any]:
    return {"subject": "child-subject", "ok": True, "case": "hit"}


@pure("p5fix.items")
def p5fix_items(_source: dict[str, Any]) -> list[dict[str, Any]]:
    return [{"item": "one"}, {"item": "two"}]


@pure("p5fix.truthy")
def p5fix_truthy(value: dict[str, Any]) -> bool:
    return bool(value.get("ok", True))


@pure("p5fix.selector")
def p5fix_selector(value: dict[str, Any]) -> str:
    return str(value.get("case", "hit"))


@pure("p5fix.report_ctx")
def p5fix_report_ctx(payload: dict[str, Any]) -> dict[str, Any]:
    result = {"ctx_seen": payload["ctx"]}
    if "item" in payload:
        result["item"] = payload["item"]
    return result


@pure("p5fix.report_parent_ctx")
def p5fix_report_parent_ctx(payload: dict[str, Any]) -> dict[str, Any]:
    return {"parent_ctx_seen": payload["ctx"]}


@pure("p5fix.wrap_items")
def p5fix_wrap_items(items: list[dict[str, Any]]) -> dict[str, Any]:
    return {"items": items}


@pure("p5fix.report_subject")
def p5fix_report_subject(subject: dict[str, Any]) -> dict[str, Any]:
    return {"subject_seen": subject["subject"]}


@pure("p5fix.report_a")
def p5fix_report_a(a: dict[str, Any]) -> dict[str, Any]:
    return {"saw": a}


def test_think_string_form_still_emits_dsl_think_directly() -> None:
    assert _canonical_ir(think("p51.reasoner")) == _canonical_ir(dsl.think("p51.reasoner"))


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

    from julep.dag import Graph, StepKind, compile

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
            child.step.reasoner
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
        match=r"unsaturated @flow application cannot be returned as runtime data",
    ):

        @flow
        def parent(source: dict[str, Any]) -> dict[str, Any]:
            y = two_params(source)
            return y


def test_pure_called_with_two_handles_gives_fix_line() -> None:
    from julep import flow, pure, tool
    from julep.define import DefineError

    @tool(effect="read", idempotent=True)
    def lk(t: str) -> dict:
        return {"a": 1, "b": 2}

    @pure("ws3_two_arg")
    def combine(a: dict, b: dict) -> dict:  # author mistakenly expects two handles
        return {**a, **b}

    with pytest.raises(DefineError, match=r"one input value.*merge.*\|"):
        @flow
        def bad(t: str) -> dict:
            hit = lk(t)
            return combine(hit, hit)   # two positional handles -> should be a DefineError


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


def test_pure_kwargs_lower_to_arr_static_args_without_std_bind() -> None:
    @flow
    def scale(source: dict[str, Any]) -> dict[str, Any]:
        scaled = p6fix_scale(source, factor=2)
        return scaled

    expected = dsl.arr("p6fix.scale", {"factor": 2})

    assert _canonical_ir(scale.to_ir()) == _canonical_ir(expected)
    assert all(node.pure != "std.bind" for node in scale.to_ir().walk())


def test_pure_kwargs_inside_flow_match_direct_pure_call() -> None:
    @flow
    def scale(source: dict[str, Any]) -> dict[str, Any]:
        scaled = p6fix_scale(source, factor=2)
        return scaled

    direct = p6fix_scale({"n": 3}, factor=2)
    authored = deploy(scale, tools=[]).dry_run({"n": 3}).value

    assert authored == direct == {"scaled": 6}


def test_pure_kwargs_with_scalar_flowing_input_do_not_bind_merge() -> None:
    @flow
    def affix(source: str) -> str:
        rendered = p6fix_affix(source, prefix=">", suffix="<")
        return rendered

    assert deploy(affix, tools=[]).dry_run("abc").value == ">abc<"


def test_multiple_pure_const_kwargs_land_in_one_args_object() -> None:
    @flow
    def scale_offset(source: dict[str, Any]) -> dict[str, Any]:
        scaled = p6fix_scale_offset(source, factor=3, offset=4)
        return scaled

    expected = dsl.arr("p6fix.scale_offset", {"factor": 3, "offset": 4})

    assert _canonical_ir(scale_offset.to_ir()) == _canonical_ir(expected)
    assert deploy(scale_offset, tools=[]).dry_run({"n": 5}).value == {"scaled": 19}


def test_pure_const_kwargs_with_name_and_ann_do_not_leak_options_into_args() -> None:
    @flow
    def named_scale(source: dict[str, Any]) -> dict[str, Any]:
        scaled = p6fix_scale(source, factor=4, name="explicit_scaled", retries=2)
        return scaled

    step = next(step for step in named_scale.graph.steps if step.ref == "p6fix.scale")

    assert step.output == "explicit_scaled"
    assert step.args == {"factor": 4}
    assert step.ann is not None
    assert step.ann.to_json() == {"maxAttempts": 2}


def test_pure_const_kwargs_keep_define_time_json_and_secret_validation() -> None:
    with pytest.raises(
        DefineError,
        match=(
            r"bound value 'factor' must be canonical JSON at .*test_define_frontend.py:\d+.*"
            r"use JSON primitives, lists, and dicts only"
        ),
    ):

        @flow
        def bad_non_json(source: dict[str, Any]) -> dict[str, Any]:
            scaled = p6fix_scale(source, factor=object())
            return scaled

    with pytest.raises(
        DefineError,
        match=(
            r"bound value 'api_key' looks secret-shaped at .*test_define_frontend.py:\d+.*"
            r"secrets belong in environment-backed tools"
        ),
    ):

        @flow
        def bad_secret(source: dict[str, Any]) -> dict[str, Any]:
            scaled = p6fix_scale(source, api_key="sk-test")
            return scaled


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
    with pytest.raises(TypeError, match=r"Handle truthiness.*<synthetic>:1.*cond\(") as truthiness:
        bool(handle)
    assert str(truthiness.value).count("<synthetic>:1") == 1
    with pytest.raises(TypeError, match=r"Handle iteration.*<synthetic>:1.*each\(") as iteration:
        iter(handle)
    assert str(iteration.value).count("<synthetic>:1") == 1
    with pytest.raises(AttributeError, match=r"Handle attribute access.*source.foo.*Use source\['foo'\]"):
        attr = "foo"
        getattr(handle, attr)
    assert not hasattr(handle, "foo")


def test_flowdef_dot_each_gives_top_level_hint() -> None:
    from julep import flow, tool
    from julep.define import DefineError

    @tool(effect="read", idempotent=True)
    def lk(t: str) -> dict:
        return {"x": 1}

    @flow
    def body(item: dict) -> dict:
        return lk("x") | item if False else item

    with pytest.raises(DefineError, match=r"each is a top-level helper.*each\(body, items"):
        @flow
        def outer(items: list) -> object:
            return body.each(items)        # method-style fan-out -> teaching error


def test_handle_dot_switch_gives_top_level_hint() -> None:
    from julep import flow, tool
    from julep.define import DefineError

    @tool(effect="read", idempotent=True)
    def lk(t: str) -> dict:
        return {"x": 1}

    with pytest.raises(DefineError, match=r"switch is a top-level helper"):
        @flow
        def outer(t: str) -> object:
            hit = lk(t)
            return hit.switch(cases={})    # method-style branch on a Handle -> teaching error


def test_handle_equality_and_inequality_raise_cond_teaching_error() -> None:
    with pytest.raises(
        DefineError,
        match=r"Handle equality comparison is not runtime data at .*test_define_frontend.py:\d+.*use cond\(",
    ):

        @flow
        def bad_eq(source: dict[str, Any], other: dict[str, Any]) -> dict[str, Any]:
            if source == other:
                out = p51_inner(source)
            else:
                out = p51_outer(other)
            return out

    with pytest.raises(
        DefineError,
        match=r"Handle equality comparison is not runtime data at .*test_define_frontend.py:\d+.*use cond\(",
    ):

        @flow
        def bad_ne(source: dict[str, Any], other: dict[str, Any]) -> dict[str, Any]:
            if source != other:
                out = p51_inner(source)
            else:
                out = p51_outer(other)
            return out

    handle = Handle.synthetic("source")
    assert {handle: "value"}[handle] == "value"


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


def test_unused_flow_parameter_is_rejected_with_location_and_policy() -> None:
    with pytest.raises(
        DefineError,
        match=(
            r"@flow function 'bad' has unused parameter 'extra' at .*test_define_frontend.py:\d+.*"
            r"@flow uses single-assignment dataflow; remove the parameter or pass it to a step"
        ),
    ):

        @flow
        def bad(source: dict[str, Any], extra: dict[str, Any]) -> dict[str, Any]:
            copied = p51_identity(source)
            return copied


def test_flow_returning_none_or_plain_value_names_return_site_and_alternative() -> None:
    with pytest.raises(
        DefineError,
        match=(
            r"@flow function 'returns_none' must return a Handle at .*test_define_frontend.py:\d+.*"
            r"return the result of a Tool, Pure, think\(\.\.\.\), h\[key\], or h1 \| h2"
        ),
    ):

        @flow
        def returns_none(source: dict[str, Any]) -> None:
            _copied = p51_identity(source)

    with pytest.raises(
        DefineError,
        match=(
            r"@flow function 'returns_plain' must return a Handle at .*test_define_frontend.py:\d+.*"
            r"return the result of a Tool, Pure, think\(\.\.\.\), h\[key\], or h1 \| h2"
        ),
    ):

        @flow
        def returns_plain(source: dict[str, Any]) -> dict[str, Any]:
            _copied = p51_identity(source)
            return {"plain": True}


def test_returning_unsaturated_bound_flow_names_return_site_and_each_alternative() -> None:
    @flow
    def two_params(source: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
        merged = source | config
        return merged

    with pytest.raises(
        DefineError,
        match=(
            r"unsaturated @flow application cannot be returned as runtime data "
            r"at .*test_define_frontend.py:\d+.*"
            r"apply it to a Handle or pass it directly to each\(body, items"
        ),
    ):

        @flow
        def bad(source: dict[str, Any]) -> object:
            return two_params(config={"limit": 3})


def test_using_unsaturated_bound_flow_as_value_names_site_and_alternative() -> None:
    @flow
    def two_params(source: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
        merged = source | config
        return merged

    with pytest.raises(
        DefineError,
        match=(
            r"unsaturated @flow application is define-time only "
            r"at .*test_define_frontend.py:\d+.*"
            r"apply it to a Handle or pass it directly to each\(body, items"
        ),
    ):

        @flow
        def bad(source: dict[str, Any]) -> dict[str, Any]:
            partial = two_params(config={"limit": 3})
            merged = source | partial
            return merged


def test_truthiness_and_iteration_inside_flow_point_at_offending_source() -> None:
    with pytest.raises(
        TypeError,
        match=r"Handle truthiness is not runtime data at .*test_define_frontend.py:\d+.*use cond\(",
    ):

        @flow
        def bad_bool(source: dict[str, Any]) -> dict[str, Any]:
            if source:
                return source
            return source

    with pytest.raises(
        TypeError,
        match=r"Handle iteration is not runtime data at .*test_define_frontend.py:\d+.*use each\(",
    ):

        @flow
        def bad_iter(source: dict[str, Any]) -> dict[str, Any]:
            for _item in source:
                return source
            return source


def test_unregistered_plain_function_message_points_to_registration_alternatives() -> None:
    def plain(value: object) -> object:
        return value

    with pytest.raises(
        DefineError,
        match=(
            r"unregistered callable 'plain' at .*test_define_frontend.py:\d+.*"
            r"decorate it with @pure or @tool, or call think\(\.\.\.\) for a reasoner step"
        ),
    ):

        @flow
        def bad(source: dict[str, Any]) -> object:
            value = plain(source)
            return value


def test_foreign_scope_handle_capture_is_rejected_at_define_time() -> None:
    foreign = Handle.synthetic("foreign")

    with pytest.raises(
        DefineError,
        match=(
            r"foreign-scope handle 'foreign' captured in @flow 'bad' "
            r"at .*test_define_frontend.py:\d+.*"
            r"pass it as a parameter or bind it through each\(body, items"
        ),
    ):

        @flow
        def bad(source: dict[str, Any]) -> dict[str, Any]:
            merged = source | foreign
            return merged


def test_non_json_and_secret_shaped_const_captures_are_define_errors() -> None:
    assert SECRET_KEY_RE.search("api_key")

    with pytest.raises(
        DefineError,
        match=(
            r"bound value 'limit' must be canonical JSON at .*test_define_frontend.py:\d+.*"
            r"use JSON primitives, lists, and dicts only"
        ),
    ):

        @flow
        def bad_non_json(source: dict[str, Any]) -> dict[str, Any]:
            copied = p51_echo_with_limit(source, limit=object())
            return copied

    with pytest.raises(
        DefineError,
        match=(
            r"bound value 'api_key' looks secret-shaped at .*test_define_frontend.py:\d+.*"
            r"secrets belong in environment-backed tools"
        ),
    ):

        @flow
        def bad_secret(source: dict[str, Any]) -> dict[str, Any]:
            copied = p51_echo_with_limit(source, api_key="sk-test")
            return copied


def test_reserved_dunder_step_names_are_rejected_before_env_collision() -> None:
    with pytest.raises(
        DefineError,
        match=r"step output name '__branch__' is reserved at .*test_define_frontend.py:\d+.*__\*__ names are internal",
    ):

        @flow
        def bad_assigned_name(source: dict[str, Any]) -> dict[str, Any]:
            __branch__ = p51_inner(source)
            return __branch__

    with pytest.raises(
        DefineError,
        match=r"step output name '__user__' is reserved at .*test_define_frontend.py:\d+.*__\*__ names are internal",
    ):

        @flow
        def bad_explicit_name(source: dict[str, Any]) -> dict[str, Any]:
            copied = p51_inner(source, name="__user__")
            return copied


def test_oversized_each_const_capture_warns_with_variable_name() -> None:
    @flow
    def label_one(cluster: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
        merged = cluster | config
        return merged

    large_config = {"payload": "x" * 5000}

    with pytest.warns(UserWarning, match=r"const capture 'config' is \d+ bytes"):

        @flow
        def labels(source: dict[str, Any]) -> dict[str, Any]:
            clusters = source["clusters"]
            out = each(label_one(config=large_config), clusters)
            return out


def test_tuple_unpacking_handle_assignment_is_rejected_with_documented_alternative() -> None:
    with pytest.raises(
        DefineError,
        match=(
            r"tuple-unpacking targets cannot bind Handle results at .*test_define_frontend.py:\d+.*"
            r"assign the step to one name or pass name="
        ),
    ):

        @flow
        def bad(source: dict[str, Any]) -> dict[str, Any]:
            left, right = p51_identity(source)
            return left | right


def test_multiline_expression_position_name_escape_and_exec_fallbacks() -> None:
    @flow
    def multiline(source: dict[str, Any]) -> dict[str, Any]:
        result = p51_outer(
            p51_inner(
                source,
            ),
        )
        return result

    assert any(step.ref == "p51.outer" and step.output == "result" for step in multiline.graph.steps)

    @flow
    def expression_position(source: dict[str, Any]) -> dict[str, Any]:
        return p51_inner(source)

    assert expression_position.graph.output_name.startswith("p51_inner_")

    @flow
    def escaped(source: dict[str, Any]) -> dict[str, Any]:
        captured = p51_inner(source, name="explicit_name")
        return captured

    assert escaped.graph.output_name == "explicit_name"

    namespace: dict[str, Any] = {"flow": flow, "p51_inner": p51_inner}
    exec(
        "from __future__ import annotations\n"
        "@flow\n"
        "def repl_like(source: dict[str, object]) -> dict[str, object]:\n"
        "    return p51_inner(source)\n",
        namespace,
    )
    repl_like = namespace["repl_like"]

    assert repl_like.graph.output_name == "p51_inner_1"


def test_single_line_each_uses_outer_assignment_name_when_body_is_bound_inline() -> None:
    @flow
    def label_one(cluster: dict[str, Any], store_context: dict[str, Any]) -> dict[str, Any]:
        payload = store_context | cluster
        label = p52_make_cluster_label(payload)
        return label

    @flow
    def label_clusters(source: dict[str, Any]) -> dict[str, Any]:
        store_context = source["store_context"]
        clusters = source["clusters"]
        labels = each(label_one(store_context=store_context), clusters, max_parallel=3)
        return labels

    assert label_clusters.graph.output_name == "labels"
    assert label_clusters.graph.steps[-1].output == "labels"


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


def test_handle_escape_to_tool_or_pure_outside_flow_is_define_error() -> None:
    handle = Handle.synthetic("source")

    with pytest.raises(
        DefineError,
        match=r"Handle escaped its @flow definition.*tool or pure was called outside @flow authoring",
    ):
        p51_echo_with_limit(handle)

    with pytest.raises(
        DefineError,
        match=r"Handle escaped its @flow definition.*tool or pure was called outside @flow authoring",
    ):
        p51_identity(handle)


def test_pure_outside_authoring_preserves_python_typeerror_for_stray_kwargs() -> None:
    with pytest.raises(TypeError, match=r"unexpected keyword argument 'limit'"):
        p51_identity({"episode_id": "ep-1"}, limit=3)


def test_saturated_multi_handle_flow_call_teaches_merge_before_inline() -> None:
    @flow
    def needs_two(source: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
        merged = source | config
        return merged

    with pytest.raises(
        DefineError,
        match=(
            r"fully bound multi-parameter @flow cannot be inlined at .*test_define_frontend.py:\d+.*"
            r"merge handles \(h1 \| h2\) into a one-parameter @flow"
        ),
    ):

        @flow
        def bad(source: dict[str, Any]) -> dict[str, Any]:
            config = p51_inner(source)
            merged = needs_two(source, config)
            return merged


def test_frontend_cond_subject_shaped_predicate_works_unmodified() -> None:
    from julep import cond

    @flow
    def found(source: dict[str, Any]) -> dict[str, Any]:
        out = p51_inner(source)
        return out

    @flow
    def missing(source: dict[str, Any]) -> dict[str, Any]:
        out = p51_outer(source)
        return out

    @flow
    def route(source: dict[str, Any]) -> dict[str, Any]:
        result = cond(p52_episode_found, source, then=found, orelse=missing)
        return result

    deployment = deploy(route, tools=[])

    assert deployment.dry_run({"found": True}).value == {"found": True, "inner": True}
    assert deployment.dry_run({"found": False}).value == {"found": False, "outer": True}


def test_qualified_and_aliased_control_helpers_are_allowed_by_identity() -> None:
    from julep import cond as c
    from julep import each as e

    @flow
    def found(source: dict[str, Any]) -> dict[str, Any]:
        out = p51_inner(source)
        return out

    @flow
    def missing(source: dict[str, Any]) -> dict[str, Any]:
        out = p51_outer(source)
        return out

    @flow
    def label_one(cluster: dict[str, Any]) -> dict[str, Any]:
        label = p52_make_cluster_label(cluster)
        return label

    @flow
    def qualified(source: dict[str, Any]) -> dict[str, Any]:
        result = ca.cond(p52_episode_found, source, then=found, orelse=missing)
        return result

    @flow
    def aliased(source: dict[str, Any]) -> dict[str, Any]:
        result = c(p52_episode_found, source, then=found, orelse=missing)
        return result

    @flow
    def aliased_each(source: dict[str, Any]) -> dict[str, Any]:
        clusters = source["clusters"]
        labels = e(label_one, clusters)
        return labels

    assert qualified.graph.output_name == "result"
    assert aliased.graph.output_name == "result"
    assert aliased_each.graph.output_name == "labels"


def test_genuinely_unregistered_qualified_callable_still_gets_existing_diagnostic() -> None:
    class Helpers:
        @staticmethod
        def plain(value: object) -> object:
            return value

    helpers = Helpers()

    with pytest.raises(
        DefineError,
        match=(
            r"unregistered callable 'helpers.plain' at .*test_define_frontend.py:\d+.*"
            r"decorate it with @pure or @tool, or call think\(\.\.\.\) for a reasoner step"
        ),
    ):

        @flow
        def bad(source: dict[str, Any]) -> object:
            value = helpers.plain(source)
            return value


def test_frontend_switch_on_cas_status_golden_and_all_arms() -> None:
    @flow
    def success(write_result: dict[str, Any]) -> dict[str, Any]:
        handled = p52_case_success(write_result)
        return handled

    @flow
    def stale(write_result: dict[str, Any]) -> dict[str, Any]:
        handled = p52_case_stale(write_result)
        return handled

    @flow
    def missing(write_result: dict[str, Any]) -> dict[str, Any]:
        handled = p52_case_missing(write_result)
        return handled

    @flow
    def default(write_result: dict[str, Any]) -> dict[str, Any]:
        handled = p52_case_default(write_result)
        return handled

    @flow
    def cas_flow(payload: dict[str, Any]) -> dict[str, Any]:
        write_result = p52_write_cas(payload)
        handled = switch(
            p52_cas_status,
            write_result,
            cases={"success": success, "stale_source": stale, "not_found": missing},
            default=default,
        )
        return handled

    expected = dsl.seq(
        dsl.call(p52_write_cas.name),
        dsl.arr("std.init", {"key": "write_result"}),
        dsl.arr("std.pack", {"fields": {"write_result": {"field": "write_result"}}}),
        dsl.par(
            dsl.ident(),
            dsl.seq(
                dsl.arr("std.pluck", {"key": "write_result"}),
                dsl.arr("p52.cas_status"),
            ),
        ),
        dsl.arr("std.assign", {"key": "__branch__"}),
        dsl.alt(
            select="std.branch_selector",
            cases={
                "success": dsl.seq(
                    dsl.arr("std.pluck", {"key": "write_result"}),
                    dsl.arr("p52.case_success"),
                ),
                "stale_source": dsl.seq(
                    dsl.arr("std.pluck", {"key": "write_result"}),
                    dsl.arr("p52.case_stale"),
                ),
                "not_found": dsl.seq(
                    dsl.arr("std.pluck", {"key": "write_result"}),
                    dsl.arr("p52.case_missing"),
                ),
            },
            default=dsl.seq(
                dsl.arr("std.pluck", {"key": "write_result"}),
                dsl.arr("p52.case_default"),
            ),
        ),
    )

    assert _canonical_ir(cas_flow.to_ir()) == _canonical_ir(expected)

    deployment = deploy(cas_flow, tools=[p52_write_cas])
    for status, expected_handled in [
        ("success", "success"),
        ("stale_source", "stale"),
        ("not_found", "missing"),
        ("rate_limited", "default"),
    ]:
        assert deployment.dry_run({"episode_id": "ep-1", "status": status}).value == {
            "handled": expected_handled,
            "episode_id": "ep-1",
        }


def test_frontend_multiple_cond_switch_labels_are_unique() -> None:
    from julep import cond

    @flow
    def yes(source: dict[str, Any]) -> dict[str, Any]:
        out = p51_inner(source)
        return out

    @flow
    def no(source: dict[str, Any]) -> dict[str, Any]:
        out = p51_outer(source)
        return out

    @flow
    def yes_first(first: dict[str, Any]) -> dict[str, Any]:
        out = p51_inner(first)
        return out

    @flow
    def no_first(first: dict[str, Any]) -> dict[str, Any]:
        out = p51_outer(first)
        return out

    @flow
    def routed(source: dict[str, Any]) -> dict[str, Any]:
        first = cond("p52.episode_found", source, then=yes, orelse=no)
        second = switch(
            "p52.cas_status",
            first,
            cases={"success": yes_first, "stale_source": no_first},
            default=no_first,
        )
        return second

    outputs = [step.output for step in routed.graph.steps]

    assert len(outputs) == len(set(outputs))


def test_cond_rejects_unregistered_pure_name_with_span_and_hint() -> None:
    @flow
    def arm(source: dict[str, Any]) -> dict[str, Any]:
        out = p51_inner(source)
        return out

    with pytest.raises(
        DefineError,
        match=(
            r"cond predicate 'missing.pure' is not a registered Pure at .*test_define_frontend.py:\d+.*"
            r"decorate a deterministic function with @pure or pass a Pure object"
        ),
    ):

        @flow
        def bad(source: dict[str, Any]) -> dict[str, Any]:
            result = cond("missing.pure", source, then=arm, orelse=arm)
            return result


def test_switch_rejects_unregistered_pure_name_with_span_and_hint() -> None:
    @flow
    def arm(source: dict[str, Any]) -> dict[str, Any]:
        out = p51_inner(source)
        return out

    with pytest.raises(
        DefineError,
        match=(
            r"switch selector 'missing.pure' is not a registered Pure at .*test_define_frontend.py:\d+.*"
            r"decorate a deterministic function with @pure or pass a Pure object"
        ),
    ):

        @flow
        def bad(source: dict[str, Any]) -> dict[str, Any]:
            result = switch("missing.pure", source, cases={"yes": arm})
            return result


def test_each_rejects_unregistered_reducer_name_with_span_and_hint() -> None:
    @flow
    def label_one(cluster: dict[str, Any]) -> dict[str, Any]:
        label = p52_make_cluster_label(cluster)
        return label

    with pytest.raises(
        DefineError,
        match=(
            r"each reducer 'missing.pure' is not a registered Pure at .*test_define_frontend.py:\d+.*"
            r"decorate a deterministic function with @pure or pass a Pure object"
        ),
    ):

        @flow
        def bad(source: dict[str, Any]) -> dict[str, Any]:
            clusters = source["clusters"]
            labels = each(label_one, clusters, reducer="missing.pure")
            return labels


def test_cond_rejects_non_pure_predicate_value_with_span_and_hint() -> None:
    @flow
    def arm(source: dict[str, Any]) -> dict[str, Any]:
        out = p51_inner(source)
        return out

    with pytest.raises(
        DefineError,
        match=(
            r"cond predicate must be a registered Pure or pure name at .*test_define_frontend.py:\d+.*"
            r"decorate a deterministic function with @pure or pass its registered name"
        ),
    ):

        @flow
        def bad(source: dict[str, Any]) -> dict[str, Any]:
            result = cond(object(), source, then=arm, orelse=arm)
            return result


def test_switch_rejects_non_pure_selector_value_with_span_and_hint() -> None:
    @flow
    def arm(source: dict[str, Any]) -> dict[str, Any]:
        out = p51_inner(source)
        return out

    with pytest.raises(
        DefineError,
        match=(
            r"switch selector must be a registered Pure or pure name at .*test_define_frontend.py:\d+.*"
            r"decorate a deterministic function with @pure or pass its registered name"
        ),
    ):

        @flow
        def bad(source: dict[str, Any]) -> dict[str, Any]:
            result = switch(object(), source, cases={"yes": arm})
            return result


def test_each_rejects_non_pure_reducer_value_with_span_and_hint() -> None:
    @flow
    def label_one(cluster: dict[str, Any]) -> dict[str, Any]:
        label = p52_make_cluster_label(cluster)
        return label

    with pytest.raises(
        DefineError,
        match=(
            r"each reducer must be a registered Pure or pure name at .*test_define_frontend.py:\d+.*"
            r"decorate a deterministic function with @pure or pass its registered name"
        ),
    ):

        @flow
        def bad(source: dict[str, Any]) -> dict[str, Any]:
            clusters = source["clusters"]
            labels = each(label_one, clusters, reducer=object())
            return labels


def test_switch_rejects_empty_cases_with_span_and_hint() -> None:
    with pytest.raises(
        DefineError,
        match=(
            r"switch needs at least one case at .*test_define_frontend.py:\d+.*"
            r"pass cases=\{key: flow, \.\.\.\} and optionally default=flow"
        ),
    ):

        @flow
        def bad(source: dict[str, Any]) -> dict[str, Any]:
            result = switch(p52_cas_status, source, cases={})
            return result


def test_cond_rejects_multi_parameter_bare_flow_arm_with_span_and_hint() -> None:
    @flow
    def multi(source: dict[str, Any], extra: dict[str, Any]) -> dict[str, Any]:
        merged = source | extra
        return merged

    @flow
    def arm(source: dict[str, Any]) -> dict[str, Any]:
        out = p51_inner(source)
        return out

    with pytest.raises(
        DefineError,
        match=(
            r"cond then arm 'multi' must be a one-parameter @flow at .*test_define_frontend.py:\d+.*"
            r"partially apply JSON or handle captures until one item parameter remains"
        ),
    ):

        @flow
        def bad(source: dict[str, Any]) -> dict[str, Any]:
            result = cond(p52_episode_found, source, then=multi, orelse=arm)
            return result


def test_switch_rejects_multi_parameter_bare_flow_arm_with_span_and_hint() -> None:
    @flow
    def multi(source: dict[str, Any], extra: dict[str, Any]) -> dict[str, Any]:
        merged = source | extra
        return merged

    with pytest.raises(
        DefineError,
        match=(
            r"switch case 'success' 'multi' must be a one-parameter @flow at .*test_define_frontend.py:\d+.*"
            r"partially apply JSON or handle captures until one item parameter remains"
        ),
    ):

        @flow
        def bad(source: dict[str, Any]) -> dict[str, Any]:
            result = switch(p52_cas_status, source, cases={"success": multi})
            return result


def test_each_rejects_bound_flow_with_multiple_remaining_parameters_with_span_and_hint() -> None:
    @flow
    def label_many(
        cluster: dict[str, Any],
        config: dict[str, Any],
        extra: dict[str, Any],
    ) -> dict[str, Any]:
        payload = cluster | config | extra
        return payload

    with pytest.raises(
        DefineError,
        match=(
            r"each body 'label_many' must leave exactly one runtime parameter at .*test_define_frontend.py:\d+.*"
            r"remaining=\['cluster', 'extra'\].*"
            r"pass a bare one-parameter @flow or bind all captures before using it"
        ),
    ):

        @flow
        def bad(source: dict[str, Any]) -> dict[str, Any]:
            clusters = source["clusters"]
            labels = each(label_many(config={"limit": 3}), clusters)
            return labels


def test_each_rejects_bound_flow_whose_remaining_parameter_is_not_first_with_span_and_hint() -> None:
    @flow
    def label_context(cluster: dict[str, Any], store_context: dict[str, Any]) -> dict[str, Any]:
        payload = cluster | store_context
        return payload

    with pytest.raises(
        DefineError,
        match=(
            r"each body 'label_context' leaves item parameter 'store_context' at .*test_define_frontend.py:\d+.*"
            r"put the item parameter first \('cluster'\) or wrap it in a one-parameter @flow"
        ),
    ):

        @flow
        def bad(source: dict[str, Any]) -> dict[str, Any]:
            clusters = source["clusters"]
            labels = each(label_context(cluster={"cluster_id": "c1"}), clusters)
            return labels


def test_each_rejects_handle_capture_label_mismatch_with_span_and_hint() -> None:
    @flow
    def label_with_context(cluster: dict[str, Any], store_context: dict[str, Any]) -> dict[str, Any]:
        payload = store_context | cluster
        return payload

    with pytest.raises(
        DefineError,
        match=(
            r"each body captures handle 'context' for parameter 'store_context' "
            r"at .*test_define_frontend.py:\d+.*"
            r"use matching Python variable names or wrap the body in a one-parameter @flow"
        ),
    ):

        @flow
        def bad(source: dict[str, Any]) -> dict[str, Any]:
            context = source["store_context"]
            clusters = source["clusters"]
            labels = each(label_with_context(store_context=context), clusters)
            return labels


def test_cond_rejects_json_capture_arm_with_span_and_hint() -> None:
    @flow
    def arm_with_limit(source: dict[str, Any], limit: dict[str, Any]) -> dict[str, Any]:
        payload = source | limit
        return payload

    @flow
    def arm(source: dict[str, Any]) -> dict[str, Any]:
        out = p51_inner(source)
        return out

    with pytest.raises(
        DefineError,
        match=(
            r"cond then arm has JSON capture 'limit' at .*test_define_frontend.py:\d+.*"
            r"wrap the arm in a one-parameter @flow or use each\(\.\.\.\) for closure conversion"
        ),
    ):

        @flow
        def bad(source: dict[str, Any]) -> dict[str, Any]:
            result = cond(p52_episode_found, source, then=arm_with_limit(limit={"limit": 3}), orelse=arm)
            return result


def test_cond_rejects_non_flow_arm_with_span_and_hint() -> None:
    def plain(value: dict[str, Any]) -> dict[str, Any]:
        return value

    @flow
    def arm(source: dict[str, Any]) -> dict[str, Any]:
        out = p51_inner(source)
        return out

    with pytest.raises(
        DefineError,
        match=(
            r"cond then arm must be an @flow function or partially applied @flow "
            r"at .*test_define_frontend.py:\d+.*decorate the body with @flow"
        ),
    ):

        @flow
        def bad(source: dict[str, Any]) -> dict[str, Any]:
            result = cond(p52_episode_found, source, then=plain, orelse=arm)
            return result


def test_each_rejects_non_flow_body_with_span_and_hint() -> None:
    def plain(value: dict[str, Any]) -> dict[str, Any]:
        return value

    with pytest.raises(
        DefineError,
        match=(
            r"each body must be an @flow function or partially applied @flow "
            r"at .*test_define_frontend.py:\d+.*decorate the body with @flow"
        ),
    ):

        @flow
        def bad(source: dict[str, Any]) -> dict[str, Any]:
            clusters = source["clusters"]
            labels = each(plain, clusters)
            return labels


def test_each_rejects_non_handle_items_inside_flow_with_span_and_hint() -> None:
    @flow
    def label_one(cluster: dict[str, Any]) -> dict[str, Any]:
        label = p52_make_cluster_label(cluster)
        return label

    with pytest.raises(
        DefineError,
        match=(
            r"each\(body, items, \.\.\.\) needs a Handle items argument inside @flow "
            r"at .*test_define_frontend.py:\d+.*"
            r"outside @flow use dsl.each\(Node, \.\.\.\) or julep.typed.each\(FlowLike, \.\.\.\)"
        ),
    ):

        @flow
        def bad(source: dict[str, Any]) -> dict[str, Any]:
            labels = each(label_one, [{"cluster_id": "c1"}])
            return labels


def test_frontend_each_with_captured_handle_golden_and_behavior() -> None:
    @flow
    def label_one(cluster: dict[str, Any], store_context: dict[str, Any]) -> dict[str, Any]:
        payload = store_context | cluster
        label = p52_make_cluster_label(payload)
        return label

    @flow
    def label_clusters(source: dict[str, Any]) -> dict[str, Any]:
        store_context = source["store_context"]
        clusters = source["clusters"]
        labels = each(
            label_one(store_context=store_context),
            clusters,
            max_parallel=2,
            reducer=p52_tally_cluster_labels,
        )
        return labels

    expected = dsl.seq(
        dsl.arr("std.init", {"key": "source"}),
        dsl.par(
            dsl.ident(),
            dsl.seq(dsl.arr("std.pluck", {"key": "source"}), dsl.arr("std.pluck", {"key": "store_context"})),
            dsl.seq(dsl.arr("std.pluck", {"key": "source"}), dsl.arr("std.pluck", {"key": "clusters"})),
        ),
        dsl.arr("std.collect", {"fields": ["store_context", "clusters"]}),
        dsl.arr(
            "std.pack",
            {"fields": {"clusters": {"field": "clusters"}, "store_context": {"field": "store_context"}}},
        ),
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
                dsl.arr("std.unpack", {"fields": {"cluster": "cluster", "store_context": "store_context"}}),
                dsl.par(
                    dsl.ident(),
                    dsl.arr("std.merge", {"fields": ["store_context", "cluster"]}),
                ),
                dsl.arr("std.assign", {"key": "payload"}),
                dsl.arr("std.pluck", {"key": "payload"}),
                dsl.arr("p52.make_cluster_label"),
            ),
            max_parallel=2,
            reducer="p52.tally_cluster_labels",
        ),
    )

    assert _canonical_ir(label_clusters.to_ir()) == _canonical_ir(expected)

    deployment = deploy(label_clusters, tools=[])
    assert deployment.dry_run(
        {
            "store_context": {"store_id": "s1"},
            "clusters": [{"cluster_id": "c1"}, {"cluster_id": "c2"}],
        }
    ).value == {"count": 2, "ids": ["c1", "c2"]}


def test_inlined_each_body_capture_collision_uses_child_binding_and_parent_stays_live() -> None:
    @flow
    def body(item: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
        payload = item | ctx
        seen = p5fix_report_ctx(payload)
        return seen

    @flow
    def child(source: dict[str, Any]) -> dict[str, Any]:
        ctx = p5fix_child_ctx(source)
        items = p5fix_items(source)
        seen = each(body(ctx=ctx), items)
        return seen

    @flow
    def parent(source: dict[str, Any]) -> dict[str, Any]:
        ctx = p5fix_parent_ctx(source)
        child_items = child(source)
        wrapped = p5fix_wrap_items(child_items)
        parent_seen = p5fix_report_parent_ctx(ctx)
        result = wrapped | parent_seen
        return result

    assert deploy(parent, tools=[]).dry_run({"ok": True}).value == {
        "items": [
            {"ctx_seen": "child-ctx", "item": "one"},
            {"ctx_seen": "child-ctx", "item": "two"},
        ],
        "parent_ctx_seen": "parent-ctx",
    }


def test_inlined_cond_arm_capture_collision_uses_child_binding() -> None:
    @flow
    def arm(source: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
        payload = source | ctx
        seen = p5fix_report_ctx(payload)
        return seen

    @flow
    def child(source: dict[str, Any]) -> dict[str, Any]:
        ctx = p5fix_child_ctx(source)
        out = cond(p5fix_truthy, source, then=arm(ctx=ctx), orelse=arm(ctx=ctx))
        return out

    @flow
    def parent(source: dict[str, Any]) -> dict[str, Any]:
        ctx = p5fix_parent_ctx(source)
        child_seen = child(source)
        parent_seen = p5fix_report_parent_ctx(ctx)
        result = child_seen | parent_seen
        return result

    assert deploy(parent, tools=[]).dry_run({"ok": True}).value == {
        "ctx_seen": "child-ctx",
        "parent_ctx_seen": "parent-ctx",
    }
    assert deploy(child, tools=[]).dry_run({"ok": True}).value == {"ctx_seen": "child-ctx"}


def test_inlined_switch_case_and_default_capture_collisions_use_child_binding() -> None:
    @flow
    def arm(source: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
        payload = source | ctx
        seen = p5fix_report_ctx(payload)
        return seen

    @flow
    def child(source: dict[str, Any]) -> dict[str, Any]:
        ctx = p5fix_child_ctx(source)
        out = switch(
            p5fix_selector,
            source,
            cases={"hit": arm(ctx=ctx)},
            default=arm(ctx=ctx),
        )
        return out

    @flow
    def parent(source: dict[str, Any]) -> dict[str, Any]:
        ctx = p5fix_parent_ctx(source)
        child_seen = child(source)
        parent_seen = p5fix_report_parent_ctx(ctx)
        result = child_seen | parent_seen
        return result

    assert deploy(parent, tools=[]).dry_run({"case": "hit"}).value["ctx_seen"] == "child-ctx"
    assert deploy(parent, tools=[]).dry_run({"case": "miss"}).value["ctx_seen"] == "child-ctx"
    assert deploy(child, tools=[]).dry_run({"case": "hit"}).value == {"ctx_seen": "child-ctx"}


def test_inlined_branch_subject_collision_keeps_arm_input_on_child_subject() -> None:
    @flow
    def cond_arm(subject: dict[str, Any]) -> dict[str, Any]:
        seen = p5fix_report_subject(subject)
        return seen

    @flow
    def switch_arm(subject: dict[str, Any]) -> dict[str, Any]:
        seen = p5fix_report_subject(subject)
        return seen

    @flow
    def child(source: dict[str, Any]) -> dict[str, Any]:
        subject = p5fix_child_subject(source)
        cond_seen = cond(p5fix_truthy, subject, then=cond_arm, orelse=cond_arm)
        switch_seen = switch(p5fix_selector, subject, cases={"hit": switch_arm}, default=switch_arm)
        result = cond_seen | switch_seen
        return result

    @flow
    def parent(source: dict[str, Any]) -> dict[str, Any]:
        subject = p5fix_parent_subject(source)
        child_seen = child(source)
        _parent_seen = p5fix_report_subject(subject)
        return child_seen

    value = deploy(parent, tools=[]).dry_run({"ok": True, "case": "hit"}).value
    assert value["subject_seen"] == "child-subject"
    assert deploy(child, tools=[]).dry_run({"ok": True, "case": "hit"}).value == {"subject_seen": "child-subject"}


def test_inlined_nested_branch_each_capture_collision_remaps_deepest_reference() -> None:
    @flow
    def body(item: dict[str, Any], subject: dict[str, Any]) -> dict[str, Any]:
        payload = item | subject
        seen = p5fix_report_subject(payload)
        return seen

    @flow
    def arm(subject: dict[str, Any]) -> dict[str, Any]:
        items = p5fix_items(subject)
        seen = each(body(subject=subject), items)
        wrapped = p5fix_wrap_items(seen)
        return wrapped

    @flow
    def child(source: dict[str, Any]) -> dict[str, Any]:
        subject = p5fix_child_subject(source)
        out = cond(p5fix_truthy, subject, then=arm, orelse=arm)
        return out

    @flow
    def parent(source: dict[str, Any]) -> dict[str, Any]:
        subject = p5fix_parent_subject(source)
        child_seen = child(source)
        _parent_seen = p5fix_report_subject(subject)
        return child_seen

    assert deploy(parent, tools=[]).dry_run({"ok": True}).value == {
        "items": [
            {"subject_seen": "child-subject"},
            {"subject_seen": "child-subject"},
        ],
    }


def test_inlined_branch_and_each_without_collisions_match_inline_authoring_ir() -> None:
    @flow
    def body(item: dict[str, Any], child_ctx: dict[str, Any]) -> dict[str, Any]:
        payload = item | child_ctx
        seen = p5fix_report_ctx(payload)
        return seen

    @flow
    def arm(source: dict[str, Any], child_ctx: dict[str, Any]) -> dict[str, Any]:
        payload = source | child_ctx
        seen = p5fix_report_ctx(payload)
        return seen

    @flow
    def child(source: dict[str, Any]) -> dict[str, Any]:
        child_ctx = p5fix_child_ctx(source)
        items = p5fix_items(source)
        seen = each(body(child_ctx=child_ctx), items)
        wrapped = p5fix_wrap_items(seen)
        routed = cond(p5fix_truthy, source, then=arm(child_ctx=child_ctx), orelse=arm(child_ctx=child_ctx))
        result = wrapped | routed
        return result

    @flow
    def parent(source: dict[str, Any]) -> dict[str, Any]:
        child_result = child(source)
        return child_result

    @flow
    def inline(source: dict[str, Any]) -> dict[str, Any]:
        child_ctx = p5fix_child_ctx(source)
        items = p5fix_items(source)
        seen = each(body(child_ctx=child_ctx), items)
        wrapped = p5fix_wrap_items(seen)
        routed = cond(p5fix_truthy, source, then=arm(child_ctx=child_ctx), orelse=arm(child_ctx=child_ctx))
        child_result = wrapped | routed
        return child_result

    assert _canonical_ir(parent.to_ir()) == _canonical_ir(inline.to_ir())
    assert deploy(parent, tools=[]).dry_run({"ok": True}).value["ctx_seen"] == "child-ctx"


def test_cond_rejects_bare_flow_arm_parameter_named_after_another_live_variable() -> None:
    @flow
    def saw_a(a: dict[str, Any]) -> dict[str, Any]:
        out = p5fix_report_a(a)
        return out

    with pytest.raises(
        DefineError,
        match=(
            r"cond then arm 'saw_a' item parameter 'a' does not match branch subject 'b' "
            r"at .*test_define_frontend.py:\d+.*"
            r"rename the arm's item parameter to 'b'.*pass name="
        ),
    ):

        @flow
        def bad(source: dict[str, Any]) -> dict[str, Any]:
            a = p5fix_parent_subject(source)
            _a_seen = p5fix_report_subject(a)
            b = p5fix_child_subject(source)
            result = cond(p5fix_truthy, b, then=saw_a, orelse=saw_a)
            return result


def test_cond_rejects_bare_flow_arm_parameter_that_matches_no_live_variable() -> None:
    @flow
    def saw_zzz(zzz: dict[str, Any]) -> dict[str, Any]:
        out = p5fix_report_a(zzz)
        return out

    with pytest.raises(
        DefineError,
        match=(
            r"cond then arm 'saw_zzz' item parameter 'zzz' does not match branch subject 'b' "
            r"at .*test_define_frontend.py:\d+.*cond/switch arms receive the branch subject"
        ),
    ):

        @flow
        def bad(source: dict[str, Any]) -> dict[str, Any]:
            b = p5fix_child_subject(source)
            result = cond(p5fix_truthy, b, then=saw_zzz, orelse=saw_zzz)
            return result


def test_switch_rejects_mismatched_case_and_default_arm_parameters() -> None:
    @flow
    def saw_a(a: dict[str, Any]) -> dict[str, Any]:
        out = p5fix_report_a(a)
        return out

    @flow
    def saw_b(b: dict[str, Any]) -> dict[str, Any]:
        out = p5fix_report_a(b)
        return out

    with pytest.raises(DefineError, match=r"switch case 'hit' 'saw_a' item parameter 'a'.*branch subject 'b'"):

        @flow
        def bad_case(source: dict[str, Any]) -> dict[str, Any]:
            b = p5fix_child_subject(source)
            result = switch(p5fix_selector, b, cases={"hit": saw_a}, default=saw_b)
            return result

    with pytest.raises(DefineError, match=r"switch default arm 'saw_a' item parameter 'a'.*branch subject 'b'"):

        @flow
        def bad_default(source: dict[str, Any]) -> dict[str, Any]:
            b = p5fix_child_subject(source)
            result = switch(p5fix_selector, b, cases={"hit": saw_b}, default=saw_a)
            return result


def test_cond_rejects_bound_flow_arm_remaining_parameter_mismatch() -> None:
    @flow
    def saw_a(a: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
        payload = a | ctx
        out = p5fix_report_ctx(payload)
        return out

    with pytest.raises(
        DefineError,
        match=r"cond then arm 'saw_a' item parameter 'a' does not match branch subject 'b'",
    ):

        @flow
        def bad(source: dict[str, Any]) -> dict[str, Any]:
            b = p5fix_child_subject(source)
            ctx = p5fix_child_ctx(source)
            result = cond(p5fix_truthy, b, then=saw_a(ctx=ctx), orelse=saw_a(ctx=ctx))
            return result


def test_cond_subject_named_with_name_escape_matches_arm_parameter() -> None:
    @flow
    def picked(picked: dict[str, Any]) -> dict[str, Any]:
        seen = p5fix_report_subject(picked)
        return seen

    @flow
    def route(source: dict[str, Any]) -> dict[str, Any]:
        subject = p5fix_child_subject(source, name="picked")
        result = cond(p5fix_truthy, subject, then=picked, orelse=picked)
        return result

    assert deploy(route, tools=[]).dry_run({"ok": True}).value == {"subject_seen": "child-subject"}


def test_each_item_parameter_can_differ_from_items_handle_label() -> None:
    @flow
    def body(item: dict[str, Any]) -> dict[str, Any]:
        seen = p5fix_report_a(item)
        return seen

    @flow
    def route(source: dict[str, Any]) -> dict[str, Any]:
        clusters = p5fix_items(source)
        result = each(body, clusters)
        return result

    assert deploy(route, tools=[]).dry_run({}).value == [
        {"saw": {"item": "one"}},
        {"saw": {"item": "two"}},
    ]


def test_exported_each_still_dispatches_to_dsl_for_node_body() -> None:
    node_each = each(dsl.arr("p51.identity"), max_parallel=2)

    assert _canonical_ir(node_each) == _canonical_ir(dsl.each(dsl.arr("p51.identity"), max_parallel=2))


def test_reschedule_lowers_to_mark_sleep_and_continue_with() -> None:
    @flow
    def wait_for_children(state: dict[str, Any]) -> dict[str, Any]:
        return reschedule(state, after_s=300, mark=p52_mark_dirty)

    ir = wait_for_children.to_ir()
    prims = [node for node in ir.walk() if isinstance(node.step, CallStep)]

    assert [step.step.tool for step in prims] == [NativeTool(p52_mark_dirty.name), NativeTool(SLEEP_TOOL)]
    assert prims[1].ann is not None and prims[1].ann.timeout == 300
    assert list(wait_for_children.to_ir().walk())[-1].pure == "std.continue_with"

    deployment = deploy(wait_for_children, tools=[p52_mark_dirty], strict=False)
    assert deployment.dry_run({"cursor": 10}).value == {"__continue__": {"cursor": 10}}


def test_reschedule_rejects_after_s_and_after_together_with_span_and_hint() -> None:
    with pytest.raises(
        DefineError,
        match=(
            r"reschedule accepts either after_s= or after=delay\(\.\.\.\), not both "
            r"at .*test_define_frontend.py:\d+"
        ),
    ):

        @flow
        def bad(state: dict[str, Any]) -> dict[str, Any]:
            result = reschedule(state, after_s=5, after=delay(seconds=5))
            return result


def test_reschedule_rejects_after_s_less_than_one_with_span_and_hint() -> None:
    with pytest.raises(
        DefineError,
        match=r"reschedule after_s must be >= 1 at .*test_define_frontend.py:\d+",
    ):

        @flow
        def bad(state: dict[str, Any]) -> dict[str, Any]:
            result = reschedule(state, after_s=0)
            return result


def test_reschedule_rejects_non_delay_after_with_span_and_hint() -> None:
    with pytest.raises(
        DefineError,
        match=(
            r"reschedule after= must be delay\(seconds=\.\.\.\) at .*test_define_frontend.py:\d+.*"
            r"use after_s=seconds or after=delay\(seconds=seconds\)"
        ),
    ):

        @flow
        def bad(state: dict[str, Any]) -> dict[str, Any]:
            result = reschedule(state, after=dsl.arr("p51.identity"))
            return result


def test_reschedule_rejects_missing_delay_with_span_and_hint() -> None:
    with pytest.raises(
        DefineError,
        match=(
            r"reschedule needs after_s=seconds or after=delay\(seconds=\.\.\.\) "
            r"at .*test_define_frontend.py:\d+"
        ),
    ):

        @flow
        def bad(state: dict[str, Any]) -> dict[str, Any]:
            result = reschedule(state)
            return result


def test_reschedule_rejects_non_tool_mark_with_span_and_hint() -> None:
    with pytest.raises(
        DefineError,
        match=(
            r"reschedule mark must be a registered Tool at .*test_define_frontend.py:\d+.*"
            r"for external dispatch, end with the dirty-mark tool and return a status"
        ),
    ):

        @flow
        def bad(state: dict[str, Any]) -> dict[str, Any]:
            result = reschedule(state, after_s=5, mark=p51_identity)
            return result
