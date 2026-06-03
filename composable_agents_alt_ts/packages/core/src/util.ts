import type { Node, NodeAnn, StepCall } from './types.js';

export function getStepToolHash(step: StepCall): string | undefined {
  return step.toolHash ?? step.frozenHash;
}

export function setStepToolHash(step: StepCall, hash: string): StepCall {
  return { ...step, toolHash: hash, frozenHash: hash };
}

export function nodeCombiner(ann: NodeAnn | undefined): NodeAnn['combiner'] | undefined {
  return ann?.combiner ?? ann?.strategy;
}

export function hedgeDelayMs(ann: NodeAnn | undefined): number | undefined {
  return ann?.hedgeMs ?? ann?.hedgeDelayMs;
}

export function nodeStopPure(node: Node): string | undefined {
  return node.stopPure ?? node.pure;
}

export function childrenOf(node: Node): Node[] {
  return [node.left, node.right, node.body, node.plan].filter((x): x is Node => Boolean(x));
}
