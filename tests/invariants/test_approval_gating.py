from __future__ import annotations

from composable_agents import (
    Brain,
    CapabilityManifest,
    Contract,
    Effect,
    HUMAN_GATE_TOOL,
    Idempotency,
    alt,
    app,
    blocking,
    call,
    deploy,
    freeze,
    human_gate,
    mcp,
    par,
    register_brain,
    register_pure,
    seq,
    stage,
    sub,
    think,
)
from composable_agents.contracts import McpAnnotations, ToolContract
from composable_agents.freeze import McpServerSnapshot, McpSnapshot, McpToolSpec, NativeToolSpec


def _pred(value):
    return bool(value)


def _register_pures() -> None:
    register_pure("b1b.pred", _pred)


def _snapshot(version: str = "1") -> McpSnapshot:
    read = McpAnnotations(read_only_hint=True, idempotent_hint=True)
    dangerous = McpAnnotations(destructive_hint=True)
    return McpSnapshot(
        servers={
            "srv": McpServerSnapshot(
                server="srv",
                version=version,
                tools={
                    "dangerous": McpToolSpec(input_schema={}, annotations=dangerous),
                    "safe": McpToolSpec(input_schema={}, annotations=read),
                },
            )
        },
        native={
            "auto": NativeToolSpec(
                input_schema={},
                contract=ToolContract(Effect.READ, Idempotency.NATIVE),
            )
        },
    )


def _diagnostic_codes(flow, *, capabilities: CapabilityManifest | None = None) -> list[str]:
    deployment = deploy(flow, _snapshot(), capabilities=capabilities, strict=False)
    return [diag.code for diag in blocking(deployment.diagnostics)]


def test_empty_tools_denies_every_tool_but_absent_tools_allows() -> None:
    flow = call(mcp("srv", "safe"))
    fr = freeze(flow, _snapshot())

    empty = CapabilityManifest.from_dict({"tools": []})
    absent = CapabilityManifest.from_dict({})

    assert "CAP_TOOL_DENIED" in [d.code for d in blocking(empty.enforce_compile(fr.flow))]
    assert not blocking(absent.enforce_compile(fr.flow))


def test_empty_brains_denies_every_brain_but_absent_brains_allows() -> None:
    flow = think("summarizer")

    empty = CapabilityManifest.from_dict({"brains": []})
    absent = CapabilityManifest.from_dict({})

    assert "CAP_MODEL_DENIED" in [d.code for d in blocking(empty.enforce_compile(flow))]
    assert not blocking(absent.enforce_compile(flow))


def test_empty_subflows_denies_every_subflow_but_absent_subflows_allows() -> None:
    flow = sub("child.flow", Contract.pipeline())

    empty = CapabilityManifest.from_dict({"subflows": []})
    absent = CapabilityManifest.from_dict({})

    assert "CAP_SUBFLOW_DENIED" in [d.code for d in blocking(empty.enforce_compile(flow))]
    assert not blocking(absent.enforce_compile(flow))


def test_models_gate_resolved_model_ids_independent_of_brain_names() -> None:
    register_brain(Brain(name="b2b.model.brain", model="model-denied", system=""))
    flow = think("b2b.model.brain")

    model_only = CapabilityManifest.from_dict({"models": ["model-allowed"]})
    absent_models = CapabilityManifest.from_dict({"brains": ["b2b.model.brain"]})
    brain_only = CapabilityManifest.from_dict(
        {"brains": ["other.brain"], "models": ["model-denied"]}
    )

    model_only_codes = [d.code for d in blocking(model_only.enforce_compile(flow))]
    brain_only_codes = [d.code for d in blocking(brain_only.enforce_compile(flow))]

    assert "CAP_MODEL_ID_DENIED" in model_only_codes
    assert "CAP_MODEL_DENIED" not in model_only_codes
    assert not blocking(absent_models.enforce_compile(flow))
    assert "CAP_MODEL_DENIED" in brain_only_codes
    assert "CAP_MODEL_ID_DENIED" not in brain_only_codes


def test_models_gate_app_controller_and_planner_brains() -> None:
    register_brain(Brain(name="b2b.model.controller", model="controller-model", system=""))
    register_brain(Brain(name="b2b.model.planner", model="planner-model", system=""))
    caps = CapabilityManifest.from_dict(
        {
            "brains": ["b2b.model.controller", "b2b.model.planner"],
            "models": ["other-model"],
        }
    )
    flow = seq(app("b2b.model.controller"), stage("b2b.model.planner"))

    codes = [d.code for d in blocking(caps.enforce_compile(flow))]

    assert codes.count("CAP_MODEL_ID_DENIED") == 2


def test_mcp_server_version_pin_accepts_satisfied_comparator() -> None:
    flow = call(mcp("srv", "safe"))
    fr = freeze(flow, _snapshot(version="2026.6"))

    caps = CapabilityManifest.from_dict({"mcp_servers": {"srv": ">=2026.5"}})

    assert not blocking(caps.enforce_compile(fr.flow, fr.manifest))


def test_mcp_server_version_pin_blocks_unsatisfied_comparator() -> None:
    fr = freeze(call(mcp("srv", "safe")), _snapshot(version="2026.4"))
    caps = CapabilityManifest.from_dict({"mcp_servers": {"srv": ">=2026.5"}})

    codes = [d.code for d in blocking(caps.enforce_compile(fr.flow, fr.manifest))]

    assert "CAP_VERSION_PIN" in codes


def test_mcp_server_version_pin_null_skips_version_check() -> None:
    fr = freeze(call(mcp("srv", "safe")), _snapshot(version="2026.4"))
    caps = CapabilityManifest.from_dict({"mcp_servers": {"srv": None}})

    assert not blocking(caps.enforce_compile(fr.flow, fr.manifest))


def test_dangerous_tool_after_human_gate_deploys_cleanly() -> None:
    deployment = deploy(seq(human_gate(), call(mcp("srv", "dangerous"))), _snapshot())

    assert not blocking(deployment.diagnostics)


def test_human_gate_after_dangerous_tool_does_not_dominate() -> None:
    codes = _diagnostic_codes(seq(call(mcp("srv", "dangerous")), human_gate()))

    assert "APPROVAL_UNGATED" in codes


def test_dangerous_alt_branch_can_be_gated_without_gating_safe_branch() -> None:
    _register_pures()
    deployment = deploy(
        alt(
            "b1b.pred",
            seq(human_gate(), call(mcp("srv", "dangerous"))),
            call(mcp("srv", "safe")),
        ),
        _snapshot(),
    )

    assert not blocking(deployment.diagnostics)


def test_partial_gate_in_alt_does_not_dominate_later_dangerous_call() -> None:
    _register_pures()

    # El Nino footgun: the "auto" alternate skips approval, so the later
    # dangerous call is reachable without a dominating human gate.
    codes = _diagnostic_codes(
        seq(
            alt("b1b.pred", human_gate(), call("auto")),
            call(mcp("srv", "dangerous")),
        )
    )

    assert "APPROVAL_UNGATED" in codes


def test_approval_true_grant_requires_a_gate_for_non_dangerous_tool() -> None:
    caps = CapabilityManifest.from_dict(
        {
            "tools": [
                {"name": "srv/safe", "effect": "read", "idempotency": "native", "approval": True},
                {"name": HUMAN_GATE_TOOL, "effect": "external", "idempotency": "none"},
            ],
            "mcp_servers": {"srv": None},
        }
    )

    assert "APPROVAL_UNGATED" in _diagnostic_codes(call(mcp("srv", "safe")), capabilities=caps)


def test_parallel_human_gate_does_not_dominate_dangerous_sibling() -> None:
    codes = _diagnostic_codes(par(human_gate(), call(mcp("srv", "dangerous"))))

    assert "APPROVAL_UNGATED" in codes


def test_subflow_boundary_does_not_supply_parent_gate() -> None:
    codes = _diagnostic_codes(
        seq(sub("child.with.internal.gate", Contract.pipeline()), call(mcp("srv", "dangerous")))
    )

    assert "APPROVAL_UNGATED" in codes
