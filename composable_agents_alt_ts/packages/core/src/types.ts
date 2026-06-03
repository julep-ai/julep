export type Json = null | boolean | number | string | Json[] | { [key: string]: Json };

export interface JSONSchema {
  $id?: string;
  $schema?: string;
  title?: string;
  description?: string;
  type?: string | string[];
  properties?: Record<string, JSONSchema>;
  required?: string[];
  additionalProperties?: boolean | JSONSchema;
  items?: JSONSchema | JSONSchema[];
  prefixItems?: JSONSchema[];
  minItems?: number;
  maxItems?: number;
  enum?: Json[];
  const?: Json;
  oneOf?: JSONSchema[];
  anyOf?: JSONSchema[];
  allOf?: JSONSchema[];
  [key: string]: unknown;
}

export type Op =
  | 'prim'
  | 'ident'
  | 'arr'
  | 'seq'
  | 'par'
  | 'alt'
  | 'iter_up_to'
  | 'eval_plan'
  | 'app';

export type Shape = 'Pipeline' | 'Dataflow' | 'Branching' | 'Feedback' | 'Staged' | 'Agent';

export const SHAPE_ORDER: readonly Shape[] = [
  'Pipeline',
  'Dataflow',
  'Branching',
  'Feedback',
  'Staged',
  'Agent'
] as const;

export type Effect = 'read' | 'write' | 'external' | 'dangerous';
export type Idempotency = 'required' | 'native' | 'best_effort' | 'none';

// `none` is the current spelling; `never` is accepted as a compatibility alias.
export type Approval = 'none' | 'never' | 'required' | 'conditional';

export interface CacheHint {
  key?: string;
  ttlSeconds?: number;
  mode?: 'none' | 'read_through' | 'write_through';
}

export interface Budget {
  maxTurns?: number;
  maxWallMs?: number;
  maxCostUsd?: number;
  maxNodes?: number;
}

export interface NodeAnn {
  name?: string;
  cost?: number;
  risk?: string;
  cache?: CacheHint;
  effect?: Effect;
  timeout?: number;
  timeoutMs?: number;
  shape?: Shape;
  shapeHint?: Shape;

  // B spelling.
  combiner?: 'race' | 'hedge' | 'quorum' | 'mapN' | 'mapReduce' | 'vote' | 'review' | 'humanGate';
  quorum?: { need: number; total: number };
  hedgeMs?: number;

  // A spelling, kept for compatibility and authoring ergonomics.
  strategy?: 'race' | 'hedge' | 'quorum' | 'vote' | 'mapN' | 'mapReduce' | 'review' | 'humanGate';
  hedgeDelayMs?: number;

  humanGate?: { signalName: string; timeoutSeconds?: number };
  degradedFrom?: Op;
  inputSchema?: JSONSchema;
  outputSchema?: JSONSchema;
}

export type ContextPolicy =
  | { kind: 'none' }
  | { kind: 'input_only' }
  | { kind: 'window'; tokens: number }
  | { kind: 'summary'; summaryRef: string }
  | { kind: 'whole_session' };

export const noContext: ContextPolicy = { kind: 'none' };
export type SummaryPolicy = 'result_only' | 'compressed_trace' | 'full_child_ref';

export type ToolRef =
  | { kind: 'native'; name: string }
  | { kind: 'mcp'; server: string; tool: string };

export interface ToolContract {
  effect: Effect;
  idempotency: Idempotency;
  approval?: Approval;
  asserted?: boolean;
}

export interface FrozenTool {
  hash: string;
  ref: ToolRef;
  inputSchema: JSONSchema;
  outputSchema?: JSONSchema;
  contract: ToolContract;
  serverVersion?: string;
  endpoint?: string;
  description?: string;
  annotations?: McpToolAnnotationHints;
  dispatch?:
    | { kind: 'http'; endpoint: string; auth?: 'bearer' | 'none'; audience?: string }
    | { kind: 'mcp'; serverUrl?: string };
}

export type ToolManifest = Record<string, FrozenTool>;

export interface StepCall {
  kind: 'call';
  tool: ToolRef;
  ctx?: ContextPolicy;
  toolHash?: string;
  frozenHash?: string;
  inputSchema?: JSONSchema;
  outputSchema?: JSONSchema;
}

export interface StepThink {
  kind: 'think';
  brain: string;
  ctx?: ContextPolicy;
  model?: string;
  modelSettings?: Record<string, unknown>;
  promptSchema?: JSONSchema;
  replySchema?: JSONSchema;
  inputSchema?: JSONSchema;
  outputSchema?: JSONSchema;
}

export interface SubContract {
  shape: Shape;
  summaryPolicy?: SummaryPolicy;
  inputSchema?: JSONSchema;
  outputSchema?: JSONSchema;
  taskQueue?: string;
  budget?: Budget;
}

export interface StepSub {
  kind: 'sub';
  ref: string;
  contract: SubContract;
  ctx?: ContextPolicy;
  inputSchema?: JSONSchema;
  outputSchema?: JSONSchema;
}

export type Step = StepCall | StepThink | StepSub;

export interface Node {
  op: Op;
  id: string;
  ann?: NodeAnn;
  step?: Step;
  left?: Node;
  right?: Node;
  bound?: number;
  body?: Node;
  plan?: Node;
  controller?: string;
  pure?: string;
  stopPure?: string;
  inputSchema?: JSONSchema;
  outputSchema?: JSONSchema;
}

export interface Diagnostic {
  severity: 'error' | 'warning' | 'info' | 'degrade';
  code: string;
  message: string;
  path: string;
  nodeId?: string;
  fix?: string;
  hint?: string;
}

export interface McpToolAnnotationHints {
  readOnlyHint?: boolean;
  destructiveHint?: boolean;
  idempotentHint?: boolean;
  openWorldHint?: boolean;
  title?: string;
  [key: string]: unknown;
}

export interface McpToolSnapshot {
  name: string;
  inputSchema: JSONSchema;
  outputSchema?: JSONSchema;
  annotations?: McpToolAnnotationHints;
  version?: string;
  description?: string;
}

export interface McpServerSnapshot {
  server: string;
  url?: string;
  version?: string;
  serverVersion?: string;
  tools: McpToolSnapshot[];
}

export interface McpSnapshot {
  servers: Record<string, McpServerSnapshot>;
}

export interface CapabilityToolOverride {
  kind?: 'native' | 'mcp';
  server?: string;
  tool?: string;
  name?: string;
  endpoint?: string;
  auth?: 'bearer' | 'none';
  audience?: string;
  effect?: Effect;
  idempotency?: Idempotency;
  approval?: Approval;
  inputSchema?: JSONSchema;
  outputSchema?: JSONSchema;
  asserted?: boolean;
  pinVersion?: boolean;
}

export interface CapabilityOverrides {
  tools?: Record<string, CapabilityToolOverride>;
  models?: string[];
  memory?: { read?: string[]; write?: string[] };
  network?: { egress?: string[] };
  mcpServers?: Record<string, { url: string; pinVersion?: boolean }>;
  budgets?: Record<Shape, Budget>;
}

export interface FreezeResult {
  flow: Node;
  manifest: ToolManifest;
  manifestHash: string;
}

export interface PlanGrants {
  toolHashes?: string[];
  toolRefs?: string[];
  maxCost?: number;
  maxNodes?: number;
  maxFanout?: number;
  maxLoopBound?: number;
  allowedModels?: string[];
}

export interface Plan {
  flow: Node;
  manifest: ToolManifest;
  manifestHash?: string;
  grants?: PlanGrants;
  budget?: Budget;
}
