"""
El Niño 2026 — Regional Agricultural Capacity-Planning Swarm
============================================================

A worked example built *on* the ``composable_agents`` framework (the canonical
Python implementation). It does not implement the framework; it imagines the
framework, the tools, and the brains all exist and composes them.

Scenario
--------
A regional growers' cooperative must plan the 2026 season under an El Niño that
is forecast to push drought into some agro-climatic zones, flood risk into
others, and heat stress across the board, with shifted rainfall timing. Finite
shared capacity — basin irrigation water, cold storage, harvest labour, drying
throughput, transport — must be allocated across zones to maximise yield and
minimise loss, then committed (water contracts, input procurement, logistics)
behind human approval.

NOTE: every climate figure below is an *illustrative planning input*, not a
forecast. The point of the example is the composition, not the meteorology.

How the topology encodes delegation principles
-----------------------------------------------
The swarm is deliberately *heterogeneous* (contingency: structure follows the
task), and the framework's primitives carry the delegation guarantees:

* Forecast ingest uses ``hedge`` over redundant providers and ``quorum`` over
  *diverse* models — systemic resilience, no cognitive monoculture (one model's
  error must not become the plan's error). Race admission guarantees these
  branches are read-only/idempotent, so cancelling a loser is safe.
* Per-zone planning fans out as ``sub`` flows — the Sub firewall keeps each
  zone's internal complexity opaque to the orchestrator (span of control: the
  controller reasons over zone *results*, not zone internals).
* High-uncertainty zones are routed to an adaptive ``app`` agent with a bounded
  budget and a closed action vocabulary; low-uncertainty zones to a
  deterministic sub-flow (graduated authority + transaction-cost economics).
* Reconciliation uses a ``stage`` — a planner brain proposes the procurement
  composition, but ``stage`` binds every call to the frozen manifest, so the
  model may choose *structure* but never a new *effect* (contract-first).
* Capital commitments (irreversible spend) sit behind a ``human_gate`` and the
  ``dangerous``/``approval: required`` capability gate — reversibility dictates
  human-in-the-loop, and the deploy-time check refuses to ship a flow that
  commits irreversible effects without one.
* Authority is *attenuated* down the chain: the capability manifest grants the
  swarm least privilege, and sub-flows/agents never receive more than they need.

Pipeline
--------
    ingest+forecast → fan-out zone planning (swarm) → reconcile vs capacity
        → human approval gate → commit & schedule
"""

from __future__ import annotations

# DSL + lifecycle surface, per the composable_agents public API.
from composable_agents import (
    Ann,
    Brain,
    Budget,
    CapabilityManifest,
    ContextScope,
    Effect,
    HUMAN_GATE_TOOL,
    Idempotency,
    McpAnnotations,
    McpServerSnapshot,
    McpSnapshot,
    McpToolSpec,
    NativeToolSpec,
    ToolContract,
    alt,
    app,
    arr,
    call,
    deploy,
    hedge,
    human_gate,
    iter_up_to,
    mcp,
    native,
    par,
    pure,
    quorum,
    register_brain,
    seq,
    stage,
    sub,
    think,
)
from composable_agents.shapes import surface_shape


ZONE_FANOUT = 12


# --------------------------------------------------------------------------- #
# 1. Pure functions — named, versioned, deterministic (Invariant 7).
#    These are the swarm's machine-checkable acceptance tests and reducers:
#    contract-first decomposition prefers outcomes a pure can verify over
#    outcomes that need a human.
# --------------------------------------------------------------------------- #
@pure("merge_forecasts.v1")
def merge_forecasts(branch_results: list[dict]) -> dict:
    """Quorum reducer: fold K successful model forecasts into one consensus.

    Diversity is the whole point — we take the *median* trajectory and flag the
    spread so disagreement surfaces instead of being averaged away.
    """
    regimes = [r["regime"] for r in branch_results]
    consensus = max(set(regimes), key=regimes.count)
    spread = 1.0 - regimes.count(consensus) / len(regimes)
    return {
        "regime": consensus,           # drought | flood | heat_stress | neutral
        "agreement": 1.0 - spread,
        "rain_anomaly_mm": sorted(r["rain_anomaly_mm"] for r in branch_results)[len(branch_results) // 2],
        "members": branch_results,
    }


@pure("zone_uncertainty_high.v1")
def zone_uncertainty_high(zone_ctx: dict) -> str:
    """Route key: which limb of the swarm plans this zone.

    Low model agreement OR a regime flip vs the historical baseline means the
    deterministic playbook is untrustworthy here — hand it to an adaptive agent.
    Everything else takes the cheaper deterministic sub-flow.
    """
    consensus = zone_ctx["forecast"]
    flipped = consensus["regime"] != zone_ctx["baseline_regime"]
    return "high" if (consensus["agreement"] < 0.66 or flipped) else "low"


@pure("classify_regime.v1")
def classify_regime(zone_ctx: dict) -> str:
    return zone_ctx["forecast"]["regime"]


@pure("allocation_feasible.v1")
def allocation_feasible(state: dict) -> bool:
    """Loop exit condition for reconciliation: does the candidate allocation fit
    inside every shared-capacity envelope AND the cash budget?"""
    cap = state["capacity"]
    alloc = state["allocation"]
    return (
        alloc["water_ML"] <= cap["water_ML"]
        and alloc["cold_storage_t"] <= cap["cold_storage_t"]
        and alloc["harvest_labour_days"] <= cap["harvest_labour_days"]
        and alloc["cost_usd"] <= state["budget_usd"]
    )


@pure("needs_human_review.v1")
def needs_human_review(plan: dict) -> str:
    """Reversibility gate. Any irreversible capital commitment above the
    delegated ceiling must go to a human — cognitive friction at the one
    junction that actually matters."""
    irreversible = plan["water_contract_usd"] + plan["procurement_usd"]
    return "review" if irreversible > plan["auto_commit_ceiling_usd"] else "auto"


@pure("is_approved.v1")
def is_approved(gate_result: dict) -> str:
    # human_gate returns {"approved": bool, "input": <plan>, ...}; on timeout it
    # preserves the input so a reviewer can still act later (spec §8.6).
    return "approved" if gate_result.get("approved") else "rejected"


def _zone_at(synthesized: dict, index: int) -> dict:
    """Select one deploy-known zone for the fixed-width swarm fan-out."""
    zone = synthesized["zones"][index]
    return {**zone, "zone_index": index, "season_context": synthesized}


@pure("zone_at_00.v1")
def zone_at_00(synthesized: dict) -> dict:
    return _zone_at(synthesized, 0)


@pure("zone_at_01.v1")
def zone_at_01(synthesized: dict) -> dict:
    return _zone_at(synthesized, 1)


@pure("zone_at_02.v1")
def zone_at_02(synthesized: dict) -> dict:
    return _zone_at(synthesized, 2)


@pure("zone_at_03.v1")
def zone_at_03(synthesized: dict) -> dict:
    return _zone_at(synthesized, 3)


@pure("zone_at_04.v1")
def zone_at_04(synthesized: dict) -> dict:
    return _zone_at(synthesized, 4)


@pure("zone_at_05.v1")
def zone_at_05(synthesized: dict) -> dict:
    return _zone_at(synthesized, 5)


@pure("zone_at_06.v1")
def zone_at_06(synthesized: dict) -> dict:
    return _zone_at(synthesized, 6)


@pure("zone_at_07.v1")
def zone_at_07(synthesized: dict) -> dict:
    return _zone_at(synthesized, 7)


@pure("zone_at_08.v1")
def zone_at_08(synthesized: dict) -> dict:
    return _zone_at(synthesized, 8)


@pure("zone_at_09.v1")
def zone_at_09(synthesized: dict) -> dict:
    return _zone_at(synthesized, 9)


@pure("zone_at_10.v1")
def zone_at_10(synthesized: dict) -> dict:
    return _zone_at(synthesized, 10)


@pure("zone_at_11.v1")
def zone_at_11(synthesized: dict) -> dict:
    return _zone_at(synthesized, 11)


ZONE_SELECTORS = tuple(f"zone_at_{i:02d}.v1" for i in range(ZONE_FANOUT))


# --------------------------------------------------------------------------- #
# 2. Brains — note the *deliberate model heterogeneity* in the forecast layer.
#    Three interpreters on three different models so a single model's blind spot
#    cannot dominate the quorum (resilience pillar 5).
# --------------------------------------------------------------------------- #
register_brain(Brain(
    name="forecast_interp_gfs",
    model="claude-opus-4-8",
    system="You read GFS-family ensemble output and classify the seasonal regime "
           "(drought|flood|heat_stress|neutral) for one zone. Be calibrated; "
           "report rain anomaly in mm and your confidence.",
    reply_schema={"regime": "str", "rain_anomaly_mm": "number", "confidence": "number"},
    tools=["weather/ensemble_gfs"],
))
register_brain(Brain(
    name="forecast_interp_ecmwf",
    model="claude-sonnet-4-6",          # different model — diversity, not monoculture
    system="Same task as the GFS interpreter, but over ECMWF-family output.",
    reply_schema={"regime": "str", "rain_anomaly_mm": "number", "confidence": "number"},
    tools=["weather/ensemble_ecmwf"],
))
register_brain(Brain(
    name="forecast_interp_regional",
    model="claude-haiku-4-5-20251001",  # third, cheaper, regionally-tuned source
    system="Same task, over the downscaled regional model for this basin.",
    reply_schema={"regime": "str", "rain_anomaly_mm": "number", "confidence": "number"},
    tools=["weather/regional_downscaled"],
))

register_brain(Brain(
    name="forecast_synthesizer",
    model="claude-opus-4-8",
    system="Given the consensus forecast and the basin's zone registry, produce "
           "a per-zone context vector: regime, baseline_regime, soil moisture, "
           "and the zone's crop calendar. Do not invent zones.",
    reply_schema={"zones": "list"},
    tools=["soil/moisture_grid", "registry/zones"],
))

register_brain(Brain(
    name="zone_agent_controller",
    model="claude-opus-4-8",
    system="You are the adaptive planner for ONE high-uncertainty zone. Each turn, "
           "either CALL one granted tool, run one SUB analysis, FINISH with a "
           "ZoneDemand, or ESCALATE if the situation is outside your competence. "
           "Prefer ESCALATE over guessing on irreversible matters.",
    reply_schema={"decision": "str", "tool": "str", "input": "any", "payload": "any"},
    tools=["soil/moisture_grid", "market/commodity_prices", "water/rights_registry"],
))

register_brain(Brain(
    name="allocation_planner",
    model="claude-opus-4-8",
    system="Given aggregate zone demand and the shared-capacity envelope, propose "
           "a PLAN that composes already-frozen tools to allocate water, storage, "
           "labour, and to stage procurement. You choose composition only; you "
           "cannot introduce tools that are not in the manifest.",
    reply_schema={"plan": "object"},
    tools=[],  # the planner reasons; the staged plan's calls bind to the manifest
))


# --------------------------------------------------------------------------- #
# 3. Tool references (frozen at deploy against the MCP snapshot / native hands).
#    Effect + idempotency + approval are declared in the capability manifest; the
#    refs here just name them.
# --------------------------------------------------------------------------- #
T_ENSEMBLE_GFS    = mcp("weather", "ensemble_gfs")
T_ENSEMBLE_ECMWF  = mcp("weather", "ensemble_ecmwf")
T_REGIONAL        = mcp("weather", "regional_downscaled")
T_ENSO_A          = mcp("weather", "enso_outlook_a")     # primary ENSO outlook
T_ENSO_B          = mcp("weather", "enso_outlook_b")     # backup provider (hedge)
T_SOIL            = mcp("soil", "moisture_grid")
T_ZONES           = mcp("registry", "zones")
T_PRICES          = mcp("market", "commodity_prices")
T_WATER_RIGHTS    = mcp("water", "rights_registry")
T_CAPACITY        = mcp("capacity", "shared_envelope")   # water/storage/labour ceilings

# Native compute hand (scale-to-zero solver). Idempotent: same demand+capacity
# in → same allocation out, so it is safe to retry liberally.
T_SOLVE           = native("optimize_allocation")

# Effectful, *irreversible* commitments — gated.
T_WATER_CONTRACT  = mcp("water", "allocate_contract")    # dangerous, approval req'd
T_PROCURE         = mcp("procure", "place_order")        # dangerous, approval req'd
T_LOGISTICS       = mcp("logistics", "book_transport")   # write, idempotent
T_IRRIGATION      = mcp("irrigation", "push_schedule")   # write, idempotent


# --------------------------------------------------------------------------- #
# 4. Forecast ingest — resilience by composition.
# --------------------------------------------------------------------------- #
# hedge: ask the primary ENSO outlook first; only spin up the backup if the
# primary is slow. Lazy branch start + first-success settlement (spec §8.3).
enso_outlook = hedge(
    [call(T_ENSO_A), call(T_ENSO_B)],
    hedge_ms=4000,
)

# quorum: three independent model+interpreter pipelines on three different
# models; accept the first 2-of-3 that succeed and reconcile with a pure.
# Diversity defeats correlated failure; quorum counts *successes*, not arrivals.
forecast_consensus = quorum(
    [
        seq(call(T_ENSEMBLE_GFS),   think("forecast_interp_gfs")),
        seq(call(T_ENSEMBLE_ECMWF), think("forecast_interp_ecmwf")),
        seq(call(T_REGIONAL),       think("forecast_interp_regional")),
    ],
    k=2,
    reduce="merge_forecasts.v1",
)

ingest = seq(
    par([enso_outlook, forecast_consensus]),     # outlook + consensus, concurrently
    # Synthesize a per-zone context vector. Annotated with a cost/timeout hint so
    # the projection can attribute spend to this step.
    think("forecast_synthesizer", ctx=ContextScope.WHOLE_SESSION,
          ann=Ann(cost_usd=0.20, timeout_s=90)),
)


# --------------------------------------------------------------------------- #
# 5. The swarm: per-zone planning.
# --------------------------------------------------------------------------- #
# 5a. Deterministic per-zone sub-flow (frozen, addressable by ref). The Sub
#     firewall makes its internals opaque to the orchestrator. It branches on the
#     zone's regime, then runs a *bounded* refinement loop — adaptive execution
#     with a hard stop, so a stuck zone can never oscillate forever.
ZONE_PLAN_REF = "zone_plan.v1"

zone_plan_flow = seq(
    alt(
        select="classify_regime.v1",
        cases={
            "drought":     seq(call(T_WATER_RIGHTS), call(T_SOIL), think("forecast_synthesizer")),
            "flood":       seq(call(T_SOIL),         think("forecast_synthesizer")),
            "heat_stress": seq(call(T_SOIL),         call(T_PRICES)),
            "neutral":     call(T_SOIL),
        },
    ),
    # Refine the zone's resource ask until it is internally feasible, capped at 3
    # rounds (Feedback shape; bounded by construction).
    iter_up_to(
        max=3,
        until="allocation_feasible.v1",
        body=call(T_SOLVE, ann=Ann(cost_usd=0.05)),
    ),
)

# 5b. Adaptive agent for high-uncertainty zones — closed vocabulary, bounded
#     budget, and an ESCALATE exit so the agent questions rather than guesses on
#     anything outside its competence (authority-gradient mitigation). The agent
#     gets *less* privilege than the orchestrator (attenuation): read-only tools
#     plus the deterministic zone plan as a callable SUB. It cannot commit spend.
zone_adaptive_agent = app(
    controller="zone_agent_controller",
    tools=["soil/moisture_grid", "market/commodity_prices", "water/rights_registry"],
    subflows=[ZONE_PLAN_REF],
    budget=Budget(usd=2.50, tokens=120_000, wall_seconds=180),
    max_rounds=8,
)

# 5c. Route each zone. Same two frozen artifacts serve every zone; the zone
#     identity rides in as the input value, so the fan-out references just two
#     things no matter how many zones there are.
def plan_one_zone(selector: str):
    return seq(
        arr(selector),
        alt(
            select="zone_uncertainty_high.v1",
            cases={
                "high": zone_adaptive_agent,   # graduated authority: agent only where warranted
                "low":  sub(ZONE_PLAN_REF),    # cheap, verifiable, opaque
            },
        ),
    )

# Fan out across the basin's zones. par over a list = concurrent swarm
# (Dataflow). Span of control stays bounded because each branch is a single
# opaque sub-result, not a tree the orchestrator has to supervise.
swarm = par([plan_one_zone(selector) for selector in ZONE_SELECTORS])


# --------------------------------------------------------------------------- #
# 6. Reconcile aggregate demand against shared capacity — staged composition.
#    The planner proposes HOW to allocate (a plan), `stage` binds its calls to
#    the frozen manifest, and a bounded loop converges to a feasible allocation.
# --------------------------------------------------------------------------- #
reconcile = seq(
    call(T_CAPACITY),                              # pull the shared-capacity envelope
    stage(planner="allocation_planner"),           # model picks composition, not effects
    iter_up_to(
        max=4,
        until="allocation_feasible.v1",
        body=call(T_SOLVE, ann=Ann(cost_usd=0.05)),
    ),
)


# --------------------------------------------------------------------------- #
# 7. Approval + commit. The dangerous, irreversible calls live *inside* the
#    approved branch of the gate — that structural dependency is what the
#    deploy-time approval check verifies (spec §7.3). Reversible scheduling
#    (logistics, irrigation) is idempotent and can run on the delegated path;
#    only irreversible spend requires human-in-the-loop.
# --------------------------------------------------------------------------- #
reversible_schedule = seq(
    call(T_LOGISTICS),                     # write, idempotent
    call(T_IRRIGATION),                    # write, idempotent
)

commit_after_human_approval = alt(
    select="is_approved.v1",
    cases={
        "approved": seq(
            call(T_WATER_CONTRACT),                # dangerous, approval-gated, idempotent
            call(T_PROCURE),                       # dangerous, approval-gated, idempotent
            reversible_schedule,
        ),
        # Rejected / timed-out: do nothing irreversible. The agent escalates the
        # plan to the cooperative's board out-of-band; we just stop here.
        "rejected": think("forecast_synthesizer"),  # placeholder no-op reasoning step
    },
)

approve_and_commit = seq(
    # Only pause a human when irreversible spend exceeds the delegated ceiling.
    alt(
        select="needs_human_review.v1",
        cases={
            "review": seq(
                human_gate(
                    prompt="Approve 2026 El Niño season capacity plan: water contract + "
                           "procurement above the delegated ceiling. Review the per-zone "
                           "allocation and the basin-level risk before signing.",
                    timeout_s=72 * 3600,           # 72h durable wait
                ),
                commit_after_human_approval,
            ),
            # Under the ceiling, only reversible/non-dangerous scheduling may run
            # without a gate. Irreversible commitments are structurally absent.
            "auto": reversible_schedule,
        },
    ),
)


# --------------------------------------------------------------------------- #
# 8. The whole program.
# --------------------------------------------------------------------------- #
season_plan = seq(
    ingest,                 # forecast (hedge + diverse quorum) → per-zone context
    swarm,                  # fan-out planning across zones (heterogeneous swarm)
    reconcile,              # stage + bounded optimisation against shared capacity
    approve_and_commit,     # human gate on irreversible spend, then commit
)


# --------------------------------------------------------------------------- #
# 9. Capability manifest — deny-by-default, least privilege, attenuated.
#    Present-but-empty = deny; absent section = unconstrained (spec §7.1).
#    Dangerous tools are pinned behind `approval: required`; expensive forecast
#    calls are rate-limited; only the frozen zone sub-flow is invokable.
# --------------------------------------------------------------------------- #
CAPS_YAML = """
budget:
  usd: 400
  tokens: 4000000
  wallSeconds: 90000

# Tools: assert effect + idempotency so the read tools are race/quorum-eligible.
tools:
  - name: weather/ensemble_gfs
    effect: read
    idempotency: native
    maxCalls: 3
  - name: weather/ensemble_ecmwf
    effect: read
    idempotency: native
    maxCalls: 3
  - name: weather/regional_downscaled
    effect: read
    idempotency: native
    maxCalls: 3
  - name: weather/enso_outlook_a
    effect: read
    idempotency: native
  - name: weather/enso_outlook_b
    effect: read
    idempotency: native
  - name: soil/moisture_grid
    effect: read
    idempotency: native
  - name: registry/zones
    effect: read
    idempotency: native
  - name: market/commodity_prices
    effect: read
    idempotency: native
  - name: water/rights_registry
    effect: read
    idempotency: native
  - name: capacity/shared_envelope
    effect: read
    idempotency: native
  - name: optimize_allocation
    effect: read
    idempotency: native
  - name: __human_gate__
    effect: external
    idempotency: none
  # Irreversible commitments: dangerous + must be human-approved + idempotent so
  # a Temporal retry can never double-sign or double-order.
  - name: water/allocate_contract
    effect: dangerous
    idempotency: required
    approval: required
    maxCalls: 1
  - name: procure/place_order
    effect: dangerous
    idempotency: required
    approval: required
    maxCalls: 1
  - name: logistics/book_transport
    effect: write
    idempotency: required
  - name: irrigation/push_schedule
    effect: write
    idempotency: native

brains:
  - forecast_interp_gfs
  - forecast_interp_ecmwf
  - forecast_interp_regional
  - forecast_synthesizer
  - zone_agent_controller
  - allocation_planner

# Attenuation: the swarm may only invoke these two frozen sub-flows, nothing else.
subflows:
  - zone_plan.v1

mcp_servers:
  weather: ">=2026.5"        # version-pinned; frozen tool server_version must match
  soil: null                 # granted, no pin
  registry: null
  market: null
  water: ">=2026.5"
  capacity: null
  procure: ">=2026.5"
  logistics: null
  irrigation: null

memory:
  - whole_session            # ContextScope.WHOLE_SESSION

network:
  - api.basin-water.gov
  - prices.agmarket.example
"""


MCP_TOOLS_BY_SERVER = {
    "weather": [
        "ensemble_gfs",
        "ensemble_ecmwf",
        "regional_downscaled",
        "enso_outlook_a",
        "enso_outlook_b",
    ],
    "soil": ["moisture_grid"],
    "registry": ["zones"],
    "market": ["commodity_prices"],
    "water": ["rights_registry", "allocate_contract"],
    "capacity": ["shared_envelope"],
    "procure": ["place_order"],
    "logistics": ["book_transport"],
    "irrigation": ["push_schedule"],
}

SERVER_VERSIONS = {
    "weather": "2026.6",
    "soil": "2026.6",
    "registry": "2026.6",
    "market": "2026.6",
    "water": "2026.6",
    "capacity": "2026.6",
    "procure": "2026.6",
    "logistics": "2026.6",
    "irrigation": "2026.6",
}


def build_release_snapshot() -> McpSnapshot:
    """Frozen release-time tool listing with versions satisfying CAPS_YAML pins."""

    read = McpAnnotations(read_only_hint=True, idempotent_hint=True)
    write = McpAnnotations(read_only_hint=False, idempotent_hint=True)
    dangerous = McpAnnotations(destructive_hint=True, idempotent_hint=True)

    annotations = {
        "water/allocate_contract": dangerous,
        "procure/place_order": dangerous,
        "logistics/book_transport": write,
        "irrigation/push_schedule": write,
    }

    servers = {}
    for server, tools in MCP_TOOLS_BY_SERVER.items():
        specs = {}
        for tool in tools:
            key = f"{server}/{tool}"
            specs[tool] = McpToolSpec(
                input_schema={},
                annotations=annotations.get(key, read),
                output_schema={},
            )
        servers[server] = McpServerSnapshot(
            server=server,
            version=SERVER_VERSIONS[server],
            tools=specs,
        )

    native = {
        "optimize_allocation": NativeToolSpec(
            input_schema={},
            contract=ToolContract(Effect.READ, Idempotency.NATIVE),
            output_schema={},
        )
    }

    return McpSnapshot(servers=servers, native=native)


def build_capabilities() -> CapabilityManifest:
    caps = CapabilityManifest.from_yaml(CAPS_YAML)
    assert HUMAN_GATE_TOOL in caps.tools
    return caps


# --------------------------------------------------------------------------- #
# 10. Build the deployment: freeze → validate → capability → race-admission.
# --------------------------------------------------------------------------- #
def build_deployment(snapshot: McpSnapshot | None = None, *, verbose: bool = False):
    """`snapshot` is the frozen MCP tool listing (server -> tool schemas/versions),
    built by the operator from live `tools/list` results at release time."""
    snapshot = snapshot or build_release_snapshot()
    caps = build_capabilities()

    # `deploy` runs the full compile pipeline and returns a Deployment carrying
    # frozen flow_json + manifest_json + diagnostics + an artifact hash.
    deployment = deploy(season_plan, snapshot, capabilities=caps, strict=False)

    blocking = [d for d in deployment.diagnostics if d.severity == "error"]
    if blocking:
        # e.g. a dangerous tool not behind a gate (RACE_SUB, CAP_*, approval),
        # an un-pinned server version, a non-race-safe quorum branch, etc.
        raise SystemExit(
            "season plan failed admission:\n  " +
            "\n  ".join(f"[{d.code}@{d.node_id}] {d.message}" for d in blocking)
        )

    deployment.surface_shape = surface_shape(deployment.flow)
    if verbose:
        print(f"deployed season_plan  artifact={deployment.artifact_hash[:12]}  "
              f"shape={deployment.surface_shape}")   # expect Agent (swarm contains app)
    return deployment


# --------------------------------------------------------------------------- #
# 11. Run it — start the workflow, service the human gate, watch the projection.
#     The operator wires the Temporal client + worker (the worker holds the real
#     MCP caller, the LLM caller, and the native-hand URLs); that wiring is the
#     deployment's responsibility and is elided here.
# --------------------------------------------------------------------------- #
async def run_season(client, snapshot, *, basin: str):
    from composable_agents import start_flow

    deployment = build_deployment(snapshot)

    handle = await start_flow(
        client,
        deployment.flow_json,
        deployment.manifest_json,
        session_id=f"season-2026-{basin}",        # workflow id == session: re-submit is deduped
        input={"basin": basin, "year": 2026, "scenario": "el_nino"},
    )

    # While the swarm runs, a review UI can poll the projection for cost-by-shape,
    # which branch won each race, which losers were cancelled, and which gate is
    # open — structural transparency for accountability.
    proj = await handle.query("projection")
    print("cost so far by shape:", proj["costByShape"])

    # Service the capital-commitment gate when (and only when) it opens.
    open_gates = await handle.query("openGates")
    for cid in open_gates:
        decision = present_to_board_and_collect(cid)   # your out-of-band review
        await handle.signal("submitHuman", {"cid": cid, "value": decision})

    result = await handle.result()
    print("committed plan:", result)
    return result


def present_to_board_and_collect(cid: str) -> dict:
    """Stand-in for the cooperative's human review. In production this is a
    durable review UI; the gate waits (up to 72h) until a real decision arrives,
    and the original plan is preserved in the gate payload either way."""
    return {"approved": True, "input": {"reviewed_by": "ops-board", "cid": cid}}


if __name__ == "__main__":
    # Sketch only — the operator supplies a connected Temporal client and the
    # frozen tool snapshot.
    #
    #   import asyncio
    #   from temporalio.client import Client
    #   snapshot = snapshot_from_listings(load_release_tool_listings())
    #   client = asyncio.run(Client.connect("temporal:7233"))
    #   asyncio.run(run_season(client, snapshot, basin="rio-verde"))
    print(__doc__)
