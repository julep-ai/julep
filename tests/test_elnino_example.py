from __future__ import annotations

import pytest

from composable_agents import (
    Ann,
    CapabilityDenied,
    CapabilityManifest,
    InMemoryEnv,
    InMemoryProjection,
    ProjectionEmitter,
    Shape,
    alt,
    bind_plan_to_manifest,
    blocking,
    call,
    check_approval_gates,
    deploy,
    get_brain,
    is_registered,
    human_gate,
    interpret,
    seq,
)
from composable_agents.shapes import surface_shape
from conftest import run
from examples.elnino import swarm


def _blocking_codes(diagnostics) -> list[str]:
    return [diag.code for diag in blocking(diagnostics)]


def test_elnino_example_deploys_cleanly_and_rejects_ungated_dangerous_path() -> None:
    snapshot = swarm.build_release_snapshot()
    caps = swarm.build_capabilities()
    deployment = swarm.build_deployment(snapshot)

    assert not blocking(deployment.diagnostics)
    assert not blocking(check_approval_gates(deployment.flow, deployment.manifest, caps))
    assert deployment.artifact_hash.startswith("sha256:")
    assert deployment.surface_shape == Shape.AGENT
    assert surface_shape(deployment.flow) == Shape.AGENT
    assert swarm.ZONE_PLAN_REF in caps.subflows
    assert all(is_registered(name) for name in _referenced_pures())
    for name in _referenced_brains():
        assert get_brain(name).name == name

    ungated = seq(
        alt(
            select="needs_human_review.v1",
            cases={
                "review": human_gate(prompt="review required"),
                "auto": call(swarm.T_LOGISTICS),
            },
        ),
        call(swarm.T_WATER_CONTRACT),
    )

    denied = deploy(ungated, snapshot, capabilities=caps, strict=False)

    assert "APPROVAL_UNGATED" in _blocking_codes(denied.diagnostics)


def test_elnino_example_runs_under_in_memory_env_with_deterministic_stubs() -> None:
    snapshot = swarm.build_release_snapshot()
    caps = swarm.build_capabilities()
    deployment = swarm.build_deployment(snapshot)
    store = InMemoryProjection()

    hands = _hands()
    brains = _brains()

    def planner(value):
        plan = call(swarm.T_SOLVE, ann=Ann(cost_usd=0.05))
        return bind_plan_to_manifest(plan, deployment.manifest)

    env = InMemoryEnv(
        deployment.manifest,
        ProjectionEmitter(store),
        hands=hands,
        brains=brains,
        subs={swarm.ZONE_PLAN_REF: _zone_sub},
        agents={"zone_agent_controller": lambda value: brains["zone_agent_controller"](value)["payload"]},
        planners={"allocation_planner": planner},
        gate=lambda value: {"approved": True, "input": value, "reviewed_by": "ops-board"},
        max_calls=caps.max_call_limits(),
    )

    result = run(
        interpret(
            deployment.flow,
            {"basin": "rio-verde", "year": 2026, "scenario": "el_nino"},
            env,
        )
    )

    assert result.value["status"] == "committed"
    assert result.value["water_contract"] == "signed"
    assert result.value["procurement_order"] == "placed"
    assert result.value["transport"] == "booked"
    assert result.value["irrigation_schedule"] == "pushed"
    assert result.value["allocation"]["cost_usd"] <= result.value["budget_usd"]
    assert any(demand["path"] == "agent" for demand in result.value["zone_demands"])
    assert any(demand["path"] == "sub" for demand in result.value["zone_demands"])
    assert store.cost_by_shape()
    assert "Pipeline" in store.cost_by_shape()

    caps.assert_within_budget(usd=399.0)
    with pytest.raises(CapabilityDenied):
        caps.assert_within_budget(usd=401.0)

    denied_caps = CapabilityManifest.from_dict({"tools": []})
    denied = deploy(swarm.season_plan, snapshot, capabilities=denied_caps, strict=False)
    assert "CAP_TOOL_DENIED" in _blocking_codes(denied.diagnostics)


def _referenced_pures() -> set[str]:
    return {
        "allocation_feasible.v1",
        "classify_regime.v1",
        "is_approved.v1",
        "merge_forecasts.v1",
        "needs_human_review.v1",
        "zone_uncertainty_high.v1",
        *swarm.ZONE_SELECTORS,
    }


def _referenced_brains() -> set[str]:
    return {
        "allocation_planner",
        "forecast_interp_ecmwf",
        "forecast_interp_gfs",
        "forecast_interp_regional",
        "forecast_synthesizer",
        "zone_agent_controller",
    }


def _zones() -> list[dict]:
    zones = []
    for index in range(swarm.ZONE_FANOUT):
        high_uncertainty = index % 3 == 0
        regime = "drought" if high_uncertainty else "neutral"
        baseline = "neutral"
        zones.append(
            {
                "zone_id": f"zone-{index:02d}",
                "baseline_regime": baseline,
                "forecast": {
                    "regime": regime,
                    "agreement": 0.55 if high_uncertainty else 0.92,
                    "rain_anomaly_mm": -80 if high_uncertainty else 5,
                },
                "soil_moisture_pct": 24 + index,
                "crop_calendar": {"planting_window": "2026-03"},
            }
        )
    return zones


def _brains():
    def synthesizer(value):
        return {
            "zones": _zones(),
            "forecast_inputs": value,
            "cost_usd": 0.20,
        }

    def zone_controller(zone):
        return {
            "decision": "FINISH",
            "payload": _zone_demand(zone, path="agent", water_ml=18),
        }

    return {
        "forecast_interp_gfs": lambda _value: _forecast_member("drought", -95, 0.81),
        "forecast_interp_ecmwf": lambda _value: _forecast_member("drought", -75, 0.78),
        "forecast_interp_regional": lambda _value: _forecast_member("heat_stress", -40, 0.69),
        "forecast_synthesizer": synthesizer,
        "zone_agent_controller": zone_controller,
        "allocation_planner": lambda _value: {"plan": "handled by planner stub"},
    }


def _forecast_member(regime: str, rain_anomaly_mm: int, confidence: float) -> dict:
    return {
        "regime": regime,
        "rain_anomaly_mm": rain_anomaly_mm,
        "confidence": confidence,
    }


def _zone_sub(zone: dict) -> dict:
    return _zone_demand(zone, path="sub", water_ml=9)


def _zone_demand(zone: dict, *, path: str, water_ml: int) -> dict:
    return {
        "zone_id": zone["zone_id"],
        "path": path,
        "demand": {
            "water_ML": water_ml,
            "cold_storage_t": 4,
            "harvest_labour_days": 6,
            "cost_usd": 1200,
        },
    }


def _hands():
    hands = {}
    for server, tools in swarm.MCP_TOOLS_BY_SERVER.items():
        for tool in tools:
            key = f"{server}/{tool}"
            hands[key] = _echo_hand(key)

    hands["capacity/shared_envelope"] = _capacity_envelope
    hands["optimize_allocation"] = _optimize_allocation
    hands["water/allocate_contract"] = _water_contract
    hands["procure/place_order"] = _procure_order
    hands["logistics/book_transport"] = _book_transport
    hands["irrigation/push_schedule"] = _push_irrigation
    return hands


def _echo_hand(key: str):
    return lambda value: {"tool": key, "input": value}


def _capacity_envelope(zone_demands: list[dict]) -> dict:
    return {
        "zone_demands": zone_demands,
        "capacity": {
            "water_ML": 240,
            "cold_storage_t": 80,
            "harvest_labour_days": 120,
        },
        "budget_usd": 300000,
    }


def _optimize_allocation(value: dict) -> dict:
    if "allocation" in value:
        return value

    return {
        **value,
        "allocation": {
            "water_ML": 180,
            "cold_storage_t": 48,
            "harvest_labour_days": 72,
            "cost_usd": 250000,
        },
        "water_contract_usd": 160000,
        "procurement_usd": 95000,
        "auto_commit_ceiling_usd": 100000,
        "status": "planned",
    }


def _plan_from_gate(value: dict) -> dict:
    return value["input"] if "input" in value else value


def _water_contract(value: dict) -> dict:
    plan = _plan_from_gate(value)
    return {**plan, "approval": value, "water_contract": "signed"}


def _procure_order(value: dict) -> dict:
    return {**value, "procurement_order": "placed"}


def _book_transport(value: dict) -> dict:
    return {**value, "transport": "booked"}


def _push_irrigation(value: dict) -> dict:
    return {**value, "irrigation_schedule": "pushed", "status": "committed"}
