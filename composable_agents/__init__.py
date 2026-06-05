"""Composable Serverless Agents — a typed, durable agent framework.

A flow is written with the combinator DSL (:func:`seq`, :func:`par`,
:func:`alt`, :func:`iter_up_to`, :func:`stage`, :func:`app`, plus the
derived :func:`race`/:func:`hedge`/:func:`quorum`/:func:`map_reduce`/…). Its
*shape* — where it sits on the Pipeline < Dataflow < Branching < Feedback <
Staged < Agent lattice — is inferred, not declared, and bounds what static
guarantees hold. :func:`deploy` freezes every tool to a content hash, validates
well-formedness, enforces capabilities (§9), and admits races (§5) before a flow
can run; :func:`freeze` and :func:`validate` are exposed for finer control.

Execution is durable on Temporal: the control plane walks the frozen IR in a
workflow, Brains and Hands are activities, Sub is a child workflow behind a
Joined firewall, and Agent is a bounded controller loop with a budget guard and
continue-as-new. That layer is imported lazily and guarded — everything in the
authoring/compile path here works with no Temporal install — and
:data:`HAVE_TEMPORAL` reports whether the runtime is available.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

__version__ = "0.1.0"

# --- shape lattice + effect kinds ----------------------------------------- #
from .kinds import (
    ContextScope as ContextScope,
    Effect as Effect,
    EnforcementMode as EnforcementMode,
    Idempotency as Idempotency,
    Shape as Shape,
    SummaryPolicy as SummaryPolicy,
)

# --- IR value types (rarely built by hand; useful for typing/introspection) #
from .ir import (
    HUMAN_GATE_TOOL as HUMAN_GATE_TOOL,
    Ann as Ann,
    CacheHint as CacheHint,
    ContextPolicy as ContextPolicy,
    McpTool as McpTool,
    NativeTool as NativeTool,
    Node as Node,
    SourceSpan as SourceSpan,
    SubContract as SubContract,
)

# --- authoring DSL --------------------------------------------------------- #
from .dsl import (
    Contract as Contract,
    alt as alt,
    app as app,
    arr as arr,
    brain_from_ctx as brain_from_ctx,
    call as call,
    fanout as fanout,
    ident as ident,
    iter_up_to as iter_up_to,
    mcp as mcp,
    native as native,
    par as par,
    seq as seq,
    set_source_capture as set_source_capture,
    source_capture_enabled as source_capture_enabled,
    stage as stage,
    sub as sub,
    think as think,
)
from .derived import (
    check_race_admission as check_race_admission,
    hedge as hedge,
    human_gate as human_gate,
    map_n as map_n,
    map_reduce as map_reduce,
    quorum as quorum,
    race as race,
    review as review,
    vote as vote,
)

# --- contracts + tool manifest --------------------------------------------- #
from .contracts import (
    FrozenTool as FrozenTool,
    McpAnnotations as McpAnnotations,
    ToolContract as ToolContract,
    ToolManifest as ToolManifest,
    definition_hash as definition_hash,
    execution_hash as execution_hash,
    manifest_from_json as manifest_from_json,
    manifest_to_json as manifest_to_json,
)

# --- compile pipeline ------------------------------------------------------ #
from .freeze import (
    CapabilityOverrides as CapabilityOverrides,
    FreezeResult as FreezeResult,
    McpServerSnapshot as McpServerSnapshot,
    McpSnapshot as McpSnapshot,
    McpToolSpec as McpToolSpec,
    NativeToolSpec as NativeToolSpec,
    freeze as freeze,
)
from .validate import Diagnostic as Diagnostic, blocking as blocking, validate as validate
from .diagnostics import explain as explain
from .capabilities import (
    Budget as Budget,
    CapabilityManifest as CapabilityManifest,
    ToolGrant as ToolGrant,
    check_approval_gates as check_approval_gates,
)
from .staged import (
    admit_plan as admit_plan,
    bind_plan_to_manifest as bind_plan_to_manifest,
    estimate_cost as estimate_cost,
    referenced_tool_keys as referenced_tool_keys,
    validate_plan as validate_plan,
)
from .deploy import (
    Deployment as Deployment,
    deploy as deploy,
    snapshot_from_listings as snapshot_from_listings,
)
from .agent import (
    AGENT_REPLY_SCHEMA as AGENT_REPLY_SCHEMA,
    Agent as Agent,
    Tool as Tool,
    snapshot_from_tools as snapshot_from_tools,
    tool as tool,
)

# --- brains (dotctx) ------------------------------------------------------- #
from .dotctx import (
    Brain as Brain,
    brain_from_settings as brain_from_settings,
    brain_to_flow as brain_to_flow,
    dotctx_flow as dotctx_flow,
    get_brain as get_brain,
    load_dotctx as load_dotctx,
    register_brain as register_brain,
)

# --- purity registry ------------------------------------------------------- #
from .purity import (
    diff_pure_hashes as diff_pure_hashes,
    get_pure as get_pure,
    is_registered as is_registered,
    pure as pure,
    register_pure as register_pure,
)
from .registry import DEFAULT_REGISTRY as DEFAULT_REGISTRY, Registry as Registry

# --- agent loop + plan extraction (P4) ------------------------------------- #
from .agent_loop import (
    AgentConfig as AgentConfig,
    AgentState as AgentState,
    Decision as Decision,
    extract_plan as extract_plan,
    generalize_trace_to_plan as generalize_trace_to_plan,
    interpret_brain_reply as interpret_brain_reply,
    promote_plan as promote_plan,
)
from .execution.cma import (
    CMAAgentEnv as CMAAgentEnv,
    CMAClient as CMAClient,
    CMAEvent as CMAEvent,
    CMASession as CMASession,
    drive_cma_agent_loop as drive_cma_agent_loop,
    manifest_to_custom_tools as manifest_to_custom_tools,
)

# --- observability projection ---------------------------------------------- #
from .projection import (
    InMemoryProjection as InMemoryProjection,
    PostgresProjection as PostgresProjection,
    ProjectionEmitter as ProjectionEmitter,
    ProjectionEvent as ProjectionEvent,
    ProjectionStore as ProjectionStore,
    SpanData as SpanData,
    ValueStore as ValueStore,
    to_otel_spans as to_otel_spans,
)

# --- errors ---------------------------------------------------------------- #
from .errors import (
    AdmissionError as AdmissionError,
    BudgetExceeded as BudgetExceeded,
    CapabilityDenied as CapabilityDenied,
    ComposableAgentsError as ComposableAgentsError,
    FreezeError as FreezeError,
    PlanRejected as PlanRejected,
    PureDriftError as PureDriftError,
    RaceAllFailed as RaceAllFailed,
    ValidationError as ValidationError,
)

# --- execution layer (always exposes the pure interpreter; Temporal guarded) #
from .execution import (
    Env as Env,
    HAVE_TEMPORAL as HAVE_TEMPORAL,
    InMemoryEnv as InMemoryEnv,
    Result as Result,
    interpret as interpret,
)

_BASE_EXPORTS = [
    # kinds
    "Shape", "Effect", "EnforcementMode", "Idempotency", "ContextScope", "SummaryPolicy",
    # ir
    "Node", "Ann", "ContextPolicy", "CacheHint", "SubContract",
    "NativeTool", "McpTool", "HUMAN_GATE_TOOL",
    # dsl
    "call", "native", "mcp", "think", "brain_from_ctx", "ident", "arr", "sub",
    "seq", "par", "fanout", "alt", "iter_up_to", "stage", "app",
    "Contract",
    # derived
    "race", "hedge", "quorum", "map_n", "map_reduce", "vote", "review",
    "human_gate", "check_race_admission",
    # contracts
    "ToolContract", "FrozenTool", "McpAnnotations", "ToolManifest",
    "definition_hash", "execution_hash", "manifest_to_json", "manifest_from_json",
    # compile
    "freeze", "FreezeResult", "McpSnapshot", "McpServerSnapshot", "McpToolSpec",
    "NativeToolSpec", "CapabilityOverrides",
    "validate", "Diagnostic", "blocking", "explain",
    "CapabilityManifest", "Budget", "ToolGrant", "check_approval_gates",
    "estimate_cost", "validate_plan", "admit_plan", "referenced_tool_keys",
    "bind_plan_to_manifest",
    "deploy", "Deployment", "snapshot_from_listings",
    "Agent", "AGENT_REPLY_SCHEMA", "Tool", "tool", "snapshot_from_tools",
    # dotctx
    "Brain", "register_brain", "get_brain", "load_dotctx", "dotctx_flow",
    "brain_to_flow", "brain_from_settings",
    # purity
    "pure", "register_pure", "is_registered", "get_pure", "diff_pure_hashes",
    "Registry", "DEFAULT_REGISTRY",
    # agent loop
    "AgentConfig", "AgentState", "Decision", "interpret_brain_reply",
    "generalize_trace_to_plan", "extract_plan", "promote_plan",
    "CMAEvent", "CMASession", "CMAClient", "CMAAgentEnv",
    "drive_cma_agent_loop", "manifest_to_custom_tools",
    # projection
    "ProjectionEvent", "ProjectionEmitter", "ProjectionStore",
    "InMemoryProjection", "PostgresProjection", "ValueStore", "SpanData",
    "to_otel_spans",
    # errors
    "ComposableAgentsError", "ValidationError", "FreezeError", "AdmissionError",
    "PureDriftError", "RaceAllFailed", "BudgetExceeded", "PlanRejected", "CapabilityDenied",
    # execution (pure)
    "Env", "InMemoryEnv", "Result", "interpret", "HAVE_TEMPORAL",
    "__version__",
]

_TEMPORAL_EXPORTS = [
    "FlowWorkflow", "AgentWorkflow", "FlowInput", "AgentInput", "ExecutionPolicy",
    "run_flow", "start_flow", "build_worker", "run_worker", "WorkerContext",
    "callHand", "invokeBrain", "compilePlan", "verifyPures", "resolveSubflow",
    "resolveAgentSpec", "resolveRuntimeCapabilities",
]


def __getattr__(name: str) -> Any:
    if name not in _TEMPORAL_EXPORTS:
        raise AttributeError(name)
    if not HAVE_TEMPORAL:
        raise AttributeError(name)
    execution = import_module(".execution", __name__)
    value = getattr(execution, name)
    globals()[name] = value
    return value


__all__ = _BASE_EXPORTS + (_TEMPORAL_EXPORTS if HAVE_TEMPORAL else [])
