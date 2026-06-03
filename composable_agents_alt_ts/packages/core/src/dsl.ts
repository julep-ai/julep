import type { ContextPolicy, JSONSchema, Node, NodeAnn, Shape, SubContract, SummaryPolicy, ToolRef } from './types.js';
import { shortHash } from './hash.js';

let nextIdCounter = 0;

export interface NodeOpts {
  id?: string;
  name?: string;
  ctx?: ContextPolicy;
  inputSchema?: JSONSchema;
  outputSchema?: JSONSchema;
  timeout?: number;
  timeoutMs?: number;
  cost?: number;
  risk?: string;
  stableIds?: boolean;
}

export interface CritiqueOpts extends NodeOpts {
  stopPure?: string;
}

export function ident(opts: NodeOpts = {}): Node {
  return base('ident', opts);
}

export function arr(pure: string, opts: NodeOpts = {}): Node {
  return { ...base('arr', opts), pure };
}

export function call(name: string, opts: NodeOpts = {}): Node {
  return prim({ kind: 'native', name }, opts);
}

export function mcpCall(server: string, tool: string, opts: NodeOpts = {}): Node {
  return prim({ kind: 'mcp', server, tool }, opts);
}

export function think(brain: string, opts: NodeOpts & { model?: string; modelSettings?: Record<string, unknown> } = {}): Node {
  const step = stripUndefined({
    kind: 'think' as const,
    brain,
    ctx: opts.ctx,
    model: opts.model,
    modelSettings: opts.modelSettings,
    promptSchema: opts.inputSchema,
    replySchema: opts.outputSchema,
    inputSchema: opts.inputSchema,
    outputSchema: opts.outputSchema
  });
  return { ...base('prim', opts), step };
}

export function brainFromCtx(path: string, opts: NodeOpts & { model?: string; modelSettings?: Record<string, unknown> } = {}): Node {
  return think(`dotctx:${path}`, opts);
}

export function subagent(ref: string, contract: SubContract, opts: NodeOpts = {}): Node {
  return {
    ...base('prim', opts),
    step: stripUndefined({
      kind: 'sub' as const,
      ref,
      contract,
      ctx: opts.ctx,
      inputSchema: opts.inputSchema ?? contract.inputSchema,
      outputSchema: opts.outputSchema ?? contract.outputSchema
    })
  };
}

export function seq(left: Node, right: Node, opts: NodeOpts | NodeAnn = {}): Node {
  return { ...base('seq', opts), left, right };
}

export function par(left: Node, right: Node, opts: NodeOpts | NodeAnn = {}): Node {
  return { ...base('par', opts), left, right };
}

export function alt(pure: string, left: Node, right: Node, opts: NodeOpts | NodeAnn = {}): Node {
  return { ...base('alt', opts), pure, left, right };
}

export function route(pure: string, left: Node, right: Node, opts: NodeOpts | NodeAnn = {}): Node {
  return alt(pure, left, right, opts);
}

export function pipeline(...nodes: Node[]): Node {
  if (nodes.length === 0) return ident();
  return nodes.reduce((a, b) => seq(a, b));
}

export function parallel(...nodes: Node[]): Node {
  if (nodes.length === 0) return ident();
  if (nodes.length === 1) return nodes[0]!;
  return nodes.reduce((a, b) => par(a, b));
}

export function fanout(...nodes: Node[]): Node {
  return parallel(...nodes);
}

export function critique(bound: number, body: Node, opts: CritiqueOpts | string = {}): Node {
  const normalized = typeof opts === 'string' ? { stopPure: opts } : opts;
  const stopPure = normalized.stopPure ?? 'critiqueConverged';
  return stripUndefined({ ...base('iter_up_to', normalized), bound, body, stopPure, pure: stopPure });
}

export function iterUpTo(bound: number, body: Node, opts: CritiqueOpts | string = {}): Node {
  return critique(bound, body, opts);
}

export function evalPlan(plan: Node, opts: NodeOpts | NodeAnn = {}): Node {
  return { ...base('eval_plan', opts), plan };
}

export function stage(controllerOrPlan: string | Node, opts: NodeOpts | NodeAnn = {}): Node {
  return typeof controllerOrPlan === 'string'
    ? { ...base('eval_plan', opts), controller: controllerOrPlan }
    : evalPlan(controllerOrPlan, opts);
}

export function escalate(controller: string, opts: NodeOpts | NodeAnn = {}): Node {
  return { ...base('app', opts), controller };
}

export const Contract = {
  pipeline(extra: Partial<SubContract> | SummaryPolicy = {}) {
    return contract('Pipeline', extra);
  },
  dataflow(extra: Partial<SubContract> | SummaryPolicy = {}) {
    return contract('Dataflow', extra);
  },
  branching(extra: Partial<SubContract> | SummaryPolicy = {}) {
    return contract('Branching', extra);
  },
  feedback(extra: Partial<SubContract> | SummaryPolicy = {}) {
    return contract('Feedback', extra);
  },
  staged(extra: Partial<SubContract> | SummaryPolicy = {}) {
    return contract('Staged', extra);
  },
  agent(extra: Partial<SubContract> | SummaryPolicy = {}) {
    return contract('Agent', extra);
  },
  of(shape: Shape, extra: Partial<SubContract> | SummaryPolicy = {}) {
    return contract(shape, extra);
  }
};

function contract(shape: Shape, extra: Partial<SubContract> | SummaryPolicy): SubContract {
  if (typeof extra === 'string') return { shape, summaryPolicy: extra };
  return { shape, ...extra };
}

function prim(tool: ToolRef, opts: NodeOpts): Node {
  const step = stripUndefined({ kind: 'call' as const, tool, ctx: opts.ctx, inputSchema: opts.inputSchema, outputSchema: opts.outputSchema });
  return { ...base('prim', opts), step };
}

function base(op: Node['op'], opts: NodeOpts | NodeAnn): Node {
  const hasOptsFields = 'ctx' in opts || 'stableIds' in opts || 'timeoutMs' in opts || 'timeout' in opts || 'inputSchema' in opts || 'outputSchema' in opts || 'id' in opts;
  const nodeOpts = opts as NodeOpts;
  const annInput = hasOptsFields
    ? stripUndefined({
        name: nodeOpts.name,
        timeout: nodeOpts.timeout,
        timeoutMs: nodeOpts.timeoutMs,
        cost: nodeOpts.cost,
        risk: nodeOpts.risk,
        inputSchema: nodeOpts.inputSchema,
        outputSchema: nodeOpts.outputSchema
      })
    : (opts as NodeAnn);

  const ann = Object.keys(annInput).length > 0 ? annInput : undefined;
  const partial = stripUndefined({ op, ann, inputSchema: nodeOpts.inputSchema, outputSchema: nodeOpts.outputSchema });
  return stripUndefined({ ...partial, id: nodeOpts.id ?? makeId(op, partial, nodeOpts.stableIds) }) as Node;
}

function makeId(prefix: string, fields: unknown, stable = true): string {
  if (stable) return `${prefix}_${shortHash({ prefix, fields })}`;
  nextIdCounter += 1;
  return `${prefix}_${nextIdCounter}_${shortHash({ prefix, nextIdCounter }, 8)}`;
}

function stripUndefined<T extends Record<string, unknown>>(obj: T): T {
  for (const key of Object.keys(obj)) {
    if (obj[key] === undefined) delete obj[key];
  }
  return obj;
}
