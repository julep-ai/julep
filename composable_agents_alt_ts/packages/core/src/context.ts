import type { Node } from './types.js';
import { cloneJson } from './stable.js';

export interface LoweringEvent {
  code: 'PAR_CTX_DEGRADED';
  nodeId: string;
  reason: string;
}

export function lowerUnsafeParContext(flow: Node): { flow: Node; events: LoweringEvent[] } {
  const events: LoweringEvent[] = [];
  return { flow: lower(cloneJson(flow)), events };

  function lower(n: Node): Node {
    if (n.left) n.left = lower(n.left);
    if (n.right) n.right = lower(n.right);
    if (n.body) n.body = lower(n.body);
    if (n.plan) n.plan = lower(n.plan);
    if (n.op === 'par' && (containsWholeSessionCtx(n.left) || containsWholeSessionCtx(n.right))) {
      events.push({ code: 'PAR_CTX_DEGRADED', nodeId: n.id, reason: 'WholeSessionCtx in a parallel branch.' });
      return { ...n, op: 'seq', ann: { ...n.ann, degradedFrom: 'par' } };
    }
    return n;
  }
}

function containsWholeSessionCtx(node: Node | undefined): boolean {
  if (!node) return false;
  const ctx = node.step && 'ctx' in node.step ? node.step.ctx : undefined;
  return ctx?.kind === 'whole_session' || containsWholeSessionCtx(node.left) || containsWholeSessionCtx(node.right) || containsWholeSessionCtx(node.body) || containsWholeSessionCtx(node.plan);
}
