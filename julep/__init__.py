"""Julep — a typed, durable agent framework.

A flow is written with the combinator DSL (:func:`seq`, :func:`par`,
:func:`each`, :func:`alt`, :func:`iter_up_to`, :func:`stage`, :func:`app`, plus the
derived :func:`race`/:func:`hedge`/:func:`quorum`/:func:`map_reduce`/…). Its
*shape* — where it sits on the Pipeline < Dataflow < Branching < Feedback <
Staged < Agent lattice — is inferred, not declared, and bounds what static
guarantees hold. :func:`deploy` freezes every tool to a content hash, validates
well-formedness, enforces capabilities (§9), and admits races (§5) before a flow
can run; :func:`freeze` and :func:`validate` are exposed for finer control.

Execution is durable on Temporal: the control plane walks the frozen IR in a
workflow, Reasoners and Tools are activities, Sub is a child workflow behind a
Joined firewall, and Agent is a bounded controller loop with a budget guard and
continue-as-new. That layer is imported lazily and guarded — everything in the
authoring/compile path here works with no Temporal install — and
:data:`HAVE_TEMPORAL` reports whether the runtime is available.
"""

from __future__ import annotations

from importlib import import_module
from importlib.metadata import PackageNotFoundError, version as _distribution_version
from types import ModuleType as _ModuleType
from typing import Any

try:
    __version__ = _distribution_version("julep")
except PackageNotFoundError:  # running from a source checkout without an install
    __version__ = "0.0.0+unknown"

# --- shape lattice + effect kinds ----------------------------------------- #
from .kinds import (
    ContextScope as ContextScope,
    Effect as Effect,
    EnforcementMode as EnforcementMode,
    Idempotency as Idempotency,
    Shape as Shape,
    SummaryPolicy as SummaryPolicy,
)

# --- IR value types (rarely built by tool; useful for typing/introspection) #
from .ir import (
    EMIT_TOOL as EMIT_TOOL,
    HUMAN_GATE_TOOL as HUMAN_GATE_TOOL,
    RECV_TOOL as RECV_TOOL,
    SLEEP_TOOL as SLEEP_TOOL,
    Ann as Ann,
    CacheHint as CacheHint,
    ChannelRef as ChannelRef,
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
    app as _dsl_app,
    arr as arr,
    reasoner_from_ctx as reasoner_from_ctx,
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
)
from .derived import (
    HUMAN_CHANNEL as HUMAN_CHANNEL,
    check_race_admission as check_race_admission,
    delay as delay,
    emit as emit,
    hedge as hedge,
    human_gate as human_gate,
    map_n as map_n,
    map_reduce as map_reduce,
    quorum as quorum,
    race as race,
    recv as recv,
    review as review,
    vote as vote,
)
from .continuation import (
    continuation_value as continuation_value,
    continue_with as continue_with,
    is_continuation as is_continuation,
    run_chained as run_chained,
)
from .session import (
    Channel as Channel,
    LocalSessionHandle as LocalSessionHandle,
    Session as Session,
    SessionCompileError as SessionCompileError,
    SessionEvent as SessionEvent,
    SessionHandle as SessionHandle,
    drive_session as drive_session,
    loop as loop,
    scan as scan,
    session as session,
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
    WorkflowStartOptions as WorkflowStartOptions,
    deploy as deploy,
    snapshot_from_listings as snapshot_from_listings,
)
from .app import (
    Application as Application,
    ApplicationDefinitionError as ApplicationDefinitionError,
    CompiledApplication as CompiledApplication,
    CompiledPipeline as CompiledPipeline,
    PipelineSpec as PipelineSpec,
)
from .app_deploy import (
    ApplicationPlan as ApplicationPlan,
    ApplicationRelease as ApplicationRelease,
    ApplicationReleaseError as ApplicationReleaseError,
    HelmLaneReconciler as HelmLaneReconciler,
    LaneObservation as LaneObservation,
    ObservedApplicationState as ObservedApplicationState,
    plan_application as plan_application,
    publish_application as publish_application,
    reconcile_application as reconcile_application,
)
from .dag import (
    Graph as Graph,
    GraphDefinitionError as GraphDefinitionError,
    InputEdge as InputEdge,
    StepKind as StepKind,
    StepNode as StepNode,
    compile as compile_dag,
    compile_env as compile_env_dag,
)
from .agent import (
    AGENT_REPLY_SCHEMA as AGENT_REPLY_SCHEMA,
    Agent as Agent,
    Tool as Tool,
    snapshot_from_tools as snapshot_from_tools,
    tool as tool,
)

# --- reasoners (dotctx) ------------------------------------------------------- #
from .dotctx import (
    Reasoner as Reasoner,
    reasoner_from_settings as reasoner_from_settings,
    reasoner_to_flow as reasoner_to_flow,
    dotctx_flow as dotctx_flow,
    get_reasoner as get_reasoner,
    load_dotctx as load_dotctx,
)

# --- purity registry ------------------------------------------------------- #
from .purity import (
    Pure as Pure,
    diff_pure_hashes as diff_pure_hashes,
    get_pure as get_pure,
    is_registered as is_registered,
    pure as pure,
    register_pure as register_pure,
)
from .registry import DEFAULT_REGISTRY as DEFAULT_REGISTRY, Registry as Registry
from . import std as _std
from .define import (
    BoundFlow as BoundFlow,
    cond as cond,
    DefineError as DefineError,
    each as each,
    FlowDef as FlowDef,
    Handle as Handle,
    flow as flow,
    reschedule as reschedule,
    switch as switch,
    switch_on as switch_on,
    think as think,
)
from .typed import as_flow as as_flow

# --- agent loop + plan extraction (P4) ------------------------------------- #
from .agent_loop import (
    AgentConfig as AgentConfig,
    AgentState as AgentState,
    Decision as Decision,
    extract_plan as extract_plan,
    generalize_trace_to_plan as generalize_trace_to_plan,
    interpret_reasoner_reply as interpret_reasoner_reply,
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
    ProjectionSink as ProjectionSink,
    ProjectionStore as ProjectionStore,
    SpanData as SpanData,
    TeeStore as TeeStore,
    ValueStore as ValueStore,
    to_otel_spans as to_otel_spans,
)

# --- provider resilience ---------------------------------------------------- #
from .resilience import (
    AttemptRecord as AttemptRecord,
    CircuitBreaker as CircuitBreaker,
    ErrorClass as ErrorClass,
    ResiliencePolicy as ResiliencePolicy,
    classify_error as classify_error,
    summarize_attempts as summarize_attempts,
)

# --- errors ---------------------------------------------------------------- #
from .errors import (
    AdmissionError as AdmissionError,
    BudgetExceeded as BudgetExceeded,
    CapabilityDenied as CapabilityDenied,
    JulepError as JulepError,
    FreezeError as FreezeError,
    PlanRejected as PlanRejected,
    PrincipalRequired as PrincipalRequired,
    PureDriftError as PureDriftError,
    RaceAllFailed as RaceAllFailed,
    ResilienceExhausted as ResilienceExhausted,
    UnsupportedShapeError as UnsupportedShapeError,
    ValidationError as ValidationError,
)

# --- execution layer (always exposes the pure interpreter; Temporal guarded) #
from .execution import (
    Env as Env,
    ExecutionPolicy as ExecutionPolicy,
    HAVE_DBOS as HAVE_DBOS,
    HAVE_TEMPORAL as HAVE_TEMPORAL,
    InMemoryEnv as InMemoryEnv,
    Result as Result,
    RunPrincipal as RunPrincipal,
    WorkerContext as WorkerContext,
    interpret as interpret,
)


class _CallableApplicationModule(_ModuleType):
    """Keep ``julep.app(...)`` compatible while exposing ``julep.app`` as a module."""

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return _dsl_app(*args, **kwargs)


# ``app`` was historically the root DSL callable, while the explicit
# application API now intentionally lives in the ``julep.app`` submodule. A
# callable module preserves both standard ``import julep.app`` semantics and
# existing ``from julep import app; app(...)`` callers.
app = import_module(".app", __name__)
app.__class__ = _CallableApplicationModule

_BASE_EXPORTS = [
    # kinds
    "Shape", "Effect", "EnforcementMode", "Idempotency", "ContextScope", "SummaryPolicy",
    # ir
    "Node", "Ann", "ContextPolicy", "CacheHint", "SubContract",
    "NativeTool", "McpTool", "ChannelRef",
    "HUMAN_GATE_TOOL", "SLEEP_TOOL", "RECV_TOOL", "EMIT_TOOL",
    # dsl
    "call", "native", "mcp", "think", "reasoner_from_ctx", "ident", "arr", "sub",
    "seq", "par", "fanout", "each", "alt", "cond", "switch", "switch_on", "reschedule",
    "iter_up_to", "stage", "app",
    "Contract",
    # derived
    "race", "hedge", "quorum", "map_n", "map_reduce", "vote", "review",
    "human_gate", "recv", "emit", "HUMAN_CHANNEL", "delay", "check_race_admission",
    # continuation
    "continue_with", "is_continuation", "continuation_value", "run_chained",
    # session
    "Channel", "Session", "SessionEvent", "SessionHandle", "LocalSessionHandle",
    "scan", "loop", "drive_session", "session", "SessionCompileError",
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
    "deploy", "Deployment", "WorkflowStartOptions", "snapshot_from_listings",
    "Application", "PipelineSpec", "CompiledApplication", "CompiledPipeline",
    "ApplicationDefinitionError", "ApplicationPlan", "ApplicationRelease",
    "ApplicationReleaseError", "HelmLaneReconciler", "LaneObservation",
    "ObservedApplicationState", "plan_application", "publish_application",
    "reconcile_application",
    "Agent", "AGENT_REPLY_SCHEMA", "Tool", "tool", "snapshot_from_tools",
    # dotctx
    "Reasoner", "get_reasoner", "load_dotctx", "dotctx_flow",
    "reasoner_to_flow", "reasoner_from_settings",
    # purity
    "pure", "register_pure", "is_registered", "get_pure", "diff_pure_hashes",
    "Registry", "DEFAULT_REGISTRY",
    # agent loop
    "AgentConfig", "AgentState", "Decision", "interpret_reasoner_reply",
    "generalize_trace_to_plan", "extract_plan", "promote_plan",
    "CMAEvent", "CMASession", "CMAClient", "CMAAgentEnv",
    "drive_cma_agent_loop", "manifest_to_custom_tools",
    # projection
    "ProjectionEvent", "ProjectionEmitter", "ProjectionSink", "ProjectionStore",
    "InMemoryProjection", "PostgresProjection", "TeeStore", "ValueStore", "SpanData",
    "to_otel_spans",
    # provider resilience
    "AttemptRecord", "CircuitBreaker", "ErrorClass", "ResiliencePolicy",
    "classify_error", "summarize_attempts",
    # errors
    "JulepError", "ValidationError", "FreezeError", "AdmissionError",
    "PureDriftError", "RaceAllFailed", "BudgetExceeded", "PlanRejected", "CapabilityDenied",
    "PrincipalRequired", "ResilienceExhausted", "UnsupportedShapeError",
    # execution (pure)
    "Env", "ExecutionPolicy", "InMemoryEnv", "Result", "RunPrincipal", "WorkerContext", "interpret",
    "HAVE_DBOS", "HAVE_TEMPORAL",
    "__version__",
]

_TEMPORAL_EXPORTS = [
    "FlowWorkflow", "SessionWorkflow", "AgentWorkflow", "FlowInput", "SessionInput", "AgentInput",
    "run_flow", "start_flow", "TemporalSessionHandle", "build_worker", "run_worker",
    "callTool", "invokeReasoner", "compilePlan", "verifyPures", "resolveSubflow",
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
