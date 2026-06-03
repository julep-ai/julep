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

# --- shape lattice + effect kinds ----------------------------------------- #
from .kinds import Shape, Effect, Idempotency, ContextScope, SummaryPolicy

# --- IR value types (rarely built by hand; useful for typing/introspection) #
from .ir import (
    Node, Ann, ContextPolicy, CacheHint, SubContract, NativeTool, McpTool,
    HUMAN_GATE_TOOL,
)

# --- authoring DSL --------------------------------------------------------- #
from .dsl import (
    call, native, mcp, think, brain_from_ctx, ident, arr, sub,
    seq, par, fanout, alt, iter_up_to, stage, app, Contract,
)
from .derived import (
    race, hedge, quorum, map_n, map_reduce, vote, review, human_gate,
    check_race_admission,
)

# --- contracts + tool manifest --------------------------------------------- #
from .contracts import (
    ToolContract, FrozenTool, McpAnnotations, ToolManifest,
    manifest_to_json, manifest_from_json,
)

# --- compile pipeline ------------------------------------------------------ #
from .freeze import (
    freeze, FreezeResult, McpSnapshot, McpServerSnapshot, McpToolSpec,
    NativeToolSpec, CapabilityOverrides,
)
from .validate import validate, Diagnostic, blocking
from .capabilities import CapabilityManifest, Budget, ToolGrant
from .staged import estimate_cost, validate_plan, admit_plan, referenced_tool_keys
from .deploy import deploy, Deployment, snapshot_from_listings

# --- brains (dotctx) ------------------------------------------------------- #
from .dotctx import (
    Brain, register_brain, get_brain, load_dotctx, dotctx_flow,
    brain_to_flow, brain_from_settings,
)

# --- purity registry ------------------------------------------------------- #
from .purity import pure, register_pure, is_registered, get_pure

# --- agent loop + plan extraction (P4) ------------------------------------- #
from .agent_loop import (
    AgentConfig, AgentState, Decision, interpret_brain_reply,
    generalize_trace_to_plan, extract_plan, promote_plan,
)

# --- observability projection ---------------------------------------------- #
from .projection import (
    ProjectionEvent, ProjectionEmitter, ProjectionStore, InMemoryProjection,
    PostgresProjection, ValueStore, SpanData, to_otel_spans,
)

# --- errors ---------------------------------------------------------------- #
from .errors import (
    ComposableAgentsError, ValidationError, FreezeError, AdmissionError,
    BudgetExceeded, PlanRejected, CapabilityDenied,
)

# --- execution layer (always exposes the pure interpreter; Temporal guarded) #
from .execution import Env, InMemoryEnv, Result, interpret, HAVE_TEMPORAL

if HAVE_TEMPORAL:  # re-export the durable runtime only when temporalio is present
    from .execution import (  # noqa: F401
        FlowWorkflow, AgentWorkflow, FlowInput, AgentInput, ExecutionPolicy,
        run_flow, start_flow, build_worker, run_worker, WorkerContext,
        callHand, invokeBrain, compilePlan, resolveSubflow, resolveAgentSpec,
    )

__version__ = "0.1.0"

_BASE_EXPORTS = [
    # kinds
    "Shape", "Effect", "Idempotency", "ContextScope", "SummaryPolicy",
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
    "manifest_to_json", "manifest_from_json",
    # compile
    "freeze", "FreezeResult", "McpSnapshot", "McpServerSnapshot", "McpToolSpec",
    "NativeToolSpec", "CapabilityOverrides",
    "validate", "Diagnostic", "blocking",
    "CapabilityManifest", "Budget", "ToolGrant",
    "estimate_cost", "validate_plan", "admit_plan", "referenced_tool_keys",
    "deploy", "Deployment", "snapshot_from_listings",
    # dotctx
    "Brain", "register_brain", "get_brain", "load_dotctx", "dotctx_flow",
    "brain_to_flow", "brain_from_settings",
    # purity
    "pure", "register_pure", "is_registered", "get_pure",
    # agent loop
    "AgentConfig", "AgentState", "Decision", "interpret_brain_reply",
    "generalize_trace_to_plan", "extract_plan", "promote_plan",
    # projection
    "ProjectionEvent", "ProjectionEmitter", "ProjectionStore",
    "InMemoryProjection", "PostgresProjection", "ValueStore", "SpanData",
    "to_otel_spans",
    # errors
    "ComposableAgentsError", "ValidationError", "FreezeError", "AdmissionError",
    "BudgetExceeded", "PlanRejected", "CapabilityDenied",
    # execution (pure)
    "Env", "InMemoryEnv", "Result", "interpret", "HAVE_TEMPORAL",
    "__version__",
]

_TEMPORAL_EXPORTS = [
    "FlowWorkflow", "AgentWorkflow", "FlowInput", "AgentInput", "ExecutionPolicy",
    "run_flow", "start_flow", "build_worker", "run_worker", "WorkerContext",
    "callHand", "invokeBrain", "compilePlan", "resolveSubflow", "resolveAgentSpec",
]

__all__ = _BASE_EXPORTS + (_TEMPORAL_EXPORTS if HAVE_TEMPORAL else [])
