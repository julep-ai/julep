import type { Budget, ContextPolicy, FrozenTool, Json, Node, Plan, PlanGrants, ToolManifest } from '@csa/core';

export interface ProjectionEnvelope {
  sessionId: string;
  workflowId?: string;
  runId?: string;
  nodeId: string;
  cid: string;
  causes: string[];
  shape?: string;
}

export interface RunInput {
  flow: Node;
  sessionId: string;
  manifest: ToolManifest;
  manifestHash: string;
  input?: Json;
  grants?: PlanGrants;
  budget?: Budget;
  appState?: AppState;
}

export interface AppState {
  turn: number;
  value?: Json;
  spentCost?: number;
}

export interface ActivityCallInput {
  cid: string;
  toolHash: string;
  input: Json;
  manifest: ToolManifest;
  sessionId: string;
  nodeId: string;
  projection?: ProjectionEnvelope;
}

export interface BrainCallInput {
  cid: string;
  brain: string;
  model?: string;
  modelSettings?: Record<string, unknown>;
  ctx?: ContextPolicy;
  input: Json;
  sessionId: string;
  nodeId: string;
  projection?: ProjectionEnvelope;
}

export interface CompilePlanInput {
  cid: string;
  controller: string;
  input: Json;
  grants: PlanGrants;
  parentManifest: ToolManifest;
  sessionId: string;
  nodeId: string;
  projection?: ProjectionEnvelope;
}

export interface RunFragment {
  flow: Node;
  manifest?: ToolManifest;
  manifestHash?: string;
  grants?: PlanGrants;
}

export interface RuntimeDeps {
  nativeRuntime?: NativeRuntime;
  mcpClient?: McpRuntime;
  brainRuntime?: BrainRuntime;
  plannerRuntime?: PlannerRuntime;
  projection?: ProjectionWriter;
}

export interface NativeRuntime {
  call(args: { endpoint: string; cid: string; input: Json; headers?: Record<string, string>; tool: FrozenTool }): Promise<Json>;
}

export interface McpRuntime {
  callTool(args: { cid: string; sessionId: string; tool: FrozenTool; input: Json }): Promise<Json>;
}

export interface BrainRuntime {
  invoke(args: { cid: string; brain: string; model?: string; modelSettings?: Record<string, unknown>; ctx?: ContextPolicy; input: Json; sessionId: string; nodeId: string }): Promise<Json>;
}

export interface PlannerRuntime {
  compile(args: { cid: string; controller: string; input: Json; sessionId: string; parentManifest: ToolManifest; grants: PlanGrants }): Promise<Plan | Node>;
}

export interface ProjectionWriter {
  planned(envelope: ProjectionEnvelope | undefined, input: Json): Promise<void>;
  did(envelope: ProjectionEnvelope | undefined, output: Json): Promise<void>;
  failed(envelope: ProjectionEnvelope | undefined, error: unknown): Promise<void>;
}
