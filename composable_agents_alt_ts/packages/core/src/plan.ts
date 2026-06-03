import type { Diagnostic, FrozenTool, Node, Plan, PlanGrants, ToolManifest } from './types.js';
import { leqShape, surfaceShape } from './shape.js';
import { validate } from './validate.js';
import { getStepToolHash } from './util.js';
import { hashManifest } from './freeze.js';

export interface PlanLimits {
  maxNodes?: number;
  maxFanout?: number;
  maxLoopBound?: number;
  maxCost?: number;
}

export function normalizePlan(planOrFlow: Plan | Node, inheritedManifest: ToolManifest = {}): Plan {
  if ('flow' in planOrFlow) {
    const manifest = planOrFlow.manifest ?? {};
    return { ...planOrFlow, manifest, manifestHash: planOrFlow.manifestHash ?? hashManifest(manifest) };
  }
  return { flow: planOrFlow, manifest: inheritedManifest, manifestHash: hashManifest(inheritedManifest) };
}

export function validatePlan(planOrFlow: Plan | Node, grants: PlanGrants = {}, parentManifest: ToolManifest = {}, limits: PlanLimits = {}): Diagnostic[] {
  const plan = normalizePlan(planOrFlow, parentManifest);
  const diags: Diagnostic[] = [];
  const mergedManifest = { ...parentManifest, ...plan.manifest };

  const shape = surfaceShape(plan.flow);
  if (!leqShape(shape, 'Feedback')) {
    diags.push({ severity: 'error', code: 'E_PLAN_AGENT', message: `model-generated plan may not introduce ${shape}; must be <= Feedback.`, path: '$.flow' });
  }

  diags.push(...validate(plan.flow, { manifest: mergedManifest, checkRaceAdmission: true }));

  const stats = collectStats(plan.flow, mergedManifest);
  const effectiveMaxNodes = limits.maxNodes ?? grants.maxNodes;
  const effectiveMaxFanout = limits.maxFanout ?? grants.maxFanout;
  const effectiveMaxLoopBound = limits.maxLoopBound ?? grants.maxLoopBound;
  const effectiveMaxCost = limits.maxCost ?? grants.maxCost;

  if (effectiveMaxNodes !== undefined && stats.nodes > effectiveMaxNodes) {
    diags.push({ severity: 'error', code: 'E_PLAN_NODE_CAP', message: `plan has ${stats.nodes} nodes; cap is ${effectiveMaxNodes}.`, path: '$.flow' });
  }
  if (effectiveMaxFanout !== undefined && stats.maxFanout > effectiveMaxFanout) {
    diags.push({ severity: 'error', code: 'E_PLAN_FANOUT_CAP', message: `plan fanout is ${stats.maxFanout}; cap is ${effectiveMaxFanout}.`, path: '$.flow' });
  }
  if (effectiveMaxLoopBound !== undefined && stats.maxLoopBound > effectiveMaxLoopBound) {
    diags.push({ severity: 'error', code: 'E_PLAN_LOOP_CAP', message: `plan loop bound is ${stats.maxLoopBound}; cap is ${effectiveMaxLoopBound}.`, path: '$.flow' });
  }
  if (effectiveMaxCost !== undefined && stats.cost > effectiveMaxCost) {
    diags.push({ severity: 'error', code: 'E_PLAN_BUDGET', message: `plan estimated cost ${stats.cost}; cap is ${effectiveMaxCost}.`, path: '$.flow' });
  }

  for (const hash of stats.toolHashes) {
    const t = mergedManifest[hash];
    const ref = t ? formatTool(t) : undefined;
    if (!isGranted(hash, ref, grants)) {
      diags.push({ severity: 'error', code: 'E_PLAN_TOOL_GRANT', message: `plan uses ungranted tool ${ref ?? hash}.`, path: '$.manifest' });
    }
  }
  return diags;
}

export function assertPlanValid(planOrFlow: Plan | Node, grants: PlanGrants = {}, parentManifest: ToolManifest = {}, limits: PlanLimits = {}): void {
  const errors = validatePlan(planOrFlow, grants, parentManifest, limits).filter((d) => d.severity === 'error');
  if (errors.length) throw new Error(errors.map((d) => `${d.code}: ${d.message}`).join('\n'));
}

function collectStats(plan: Node, manifest: ToolManifest) {
  let nodes = 0;
  let maxFanout = 1;
  let maxLoopBound = 0;
  let cost = 0;
  const toolHashes = new Set<string>();

  walk(plan);
  return { nodes, maxFanout, maxLoopBound, cost, toolHashes };

  function walk(n: Node): number {
    nodes += 1;
    cost += n.ann?.cost ?? 0;
    if (n.op === 'prim' && n.step?.kind === 'call') {
      const hash = getStepToolHash(n.step);
      if (hash && manifest[hash]) toolHashes.add(hash);
    }
    if (n.op === 'iter_up_to') maxLoopBound = Math.max(maxLoopBound, n.bound ?? 0);
    const childCounts = [n.left, n.right, n.body, n.plan].filter(Boolean).map((c) => walk(c as Node));
    if (n.op === 'par') maxFanout = Math.max(maxFanout, childCounts.reduce((a, b) => a + b, 0));
    return n.op === 'par' ? childCounts.reduce((a, b) => a + b, 0) : 1;
  }
}

function isGranted(hash: string, ref: string | undefined, grants: PlanGrants): boolean {
  if (!grants.toolHashes?.length && !grants.toolRefs?.length) return true;
  return Boolean(grants.toolHashes?.includes(hash) || (ref && grants.toolRefs?.includes(ref)));
}

function formatTool(tool: FrozenTool): string {
  return tool.ref.kind === 'native' ? tool.ref.name : `${tool.ref.server}/${tool.ref.tool}`;
}
