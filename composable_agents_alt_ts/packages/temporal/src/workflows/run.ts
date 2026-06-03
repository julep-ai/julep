import { proxyActivities, executeChild, continueAsNew, workflowInfo, sleep } from '@temporalio/workflow';
import type { Json, Node, Plan, ToolManifest } from '@csa/core';
import { getPure, getStepToolHash, hedgeDelayMs, nodeCombiner, nodeStopPure, normalizePlan, tinyStableHash, validatePlan } from '@csa/core/workflow';
import type { ActivityCallInput, BrainCallInput, CompilePlanInput, ProjectionEnvelope, RunInput } from '../types.js';

const activities = proxyActivities<{
  callHand(input: ActivityCallInput): Promise<Json>;
  invokeBrain(input: BrainCallInput): Promise<Json>;
  compilePlan(input: CompilePlanInput): Promise<Plan>;
}>({
  startToCloseTimeout: '2 minutes',
  heartbeatTimeout: '30 seconds',
  retry: { maximumAttempts: 3 }
});

export async function run(input: RunInput): Promise<Json> {
  return await evalNode(input.flow, (input.input ?? null) as Json, input, []);
}

async function evalNode(node: Node, value: Json, runInput: RunInput, causes: string[]): Promise<Json> {
  switch (node.op) {
    case 'ident':
      return value;
    case 'arr': {
      const fn = getPure(required(node.pure, node, 'pure'));
      return fn(value) as Json;
    }
    case 'seq': {
      const a = await evalNode(required(node.left, node, 'left'), value, runInput, causes);
      return await evalNode(required(node.right, node, 'right'), a, runInput, causes);
    }
    case 'par':
      return await evalPar(node, value, runInput, causes);
    case 'alt': {
      const pred = getPure(required(node.pure, node, 'pure'));
      return (pred(value) as boolean)
        ? evalNode(required(node.left, node, 'left'), value, runInput, causes)
        : evalNode(required(node.right, node, 'right'), value, runInput, causes);
    }
    case 'iter_up_to': {
      let v = value;
      const body = required(node.body, node, 'body');
      for (let i = 0; i < required(node.bound, node, 'bound'); i++) {
        v = await evalNode(body, v, runInput, [node.id, `${node.id}:iter:${i}`]);
        const stop = nodeStopPure(node);
        if (stop && (getPure(stop)(v) as boolean)) break;
      }
      return v;
    }
    case 'prim':
      return await runStep(node, value, runInput, causes);
    case 'eval_plan': {
      const plan = node.plan
        ? normalizePlan({ flow: node.plan, manifest: {}, grants: runInput.grants }, runInput.manifest)
        : await activities.compilePlan({
            cid: stableCallId(node, value, runInput.manifestHash),
            controller: required(node.controller, node, 'controller'),
            input: value,
            grants: runInput.grants ?? {},
            parentManifest: runInput.manifest,
            sessionId: runInput.sessionId,
            nodeId: node.id,
            projection: projection(runInput, node, stableCallId(node, value, runInput.manifestHash), causes)
          });
      const normalized = normalizePlan(plan, runInput.manifest);
      const diags = validatePlan(normalized, runInput.grants ?? {}, runInput.manifest);
      const errors = diags.filter((d) => d.severity === 'error');
      if (errors.length > 0) throw new Error(`Invalid generated plan: ${errors.map((e) => `${e.code}:${e.message}`).join('; ')}`);
      const mergedManifest = { ...runInput.manifest, ...normalized.manifest };
      const nextRun = { ...runInput, manifest: mergedManifest, manifestHash: stableManifestHash(mergedManifest), grants: normalized.grants ?? runInput.grants };
      return await evalNode(normalized.flow, value, nextRun, [node.id]);
    }
    case 'app':
      return await runApp(node, value, runInput, causes);
    default:
      throw new Error(`Unknown op ${(node as Node).op}`);
  }
}

async function evalPar(node: Node, value: Json, runInput: RunInput, causes: string[]): Promise<Json> {
  const branches = flattenPar(node);
  switch (nodeCombiner(node.ann)) {
    case 'race':
      return await Promise.any(branches.map((b) => evalNode(b, value, runInput, causes)));
    case 'hedge': {
      const [primary, fallback] = branches;
      if (!primary || !fallback || branches.length !== 2) throw new Error(`hedge node ${node.id} requires exactly two branches`);
      return await Promise.any([
        evalNode(primary, value, runInput, causes),
        (async () => {
          await sleep(hedgeDelayMs(node.ann) ?? 0);
          return evalNode(fallback, value, runInput, causes);
        })()
      ]);
    }
    case 'quorum': {
      const need = node.ann?.quorum?.need ?? branches.length;
      const settled = await Promise.allSettled(branches.map((b) => evalNode(b, value, runInput, causes)));
      const successes = settled.filter((s): s is PromiseFulfilledResult<Json> => s.status === 'fulfilled').map((s) => s.value);
      if (successes.length < need) throw new Error(`quorum failed: need ${need}, got ${successes.length}`);
      return successes.slice(0, need) as Json;
    }
    default:
      return await Promise.all(branches.map((b) => evalNode(b, value, runInput, causes))) as Json;
  }
}

async function runStep(node: Node, value: Json, runInput: RunInput, causes: string[]): Promise<Json> {
  if (!node.step) throw new Error(`prim node ${node.id} missing step`);
  const cid = stableCallId(node, value, runInput.manifestHash);
  switch (node.step.kind) {
    case 'call': {
      const hash = getStepToolHash(node.step);
      if (!hash) throw new Error(`call node ${node.id} is not frozen`);
      return await activities.callHand({
        cid,
        toolHash: hash,
        input: value,
        manifest: runInput.manifest,
        sessionId: runInput.sessionId,
        nodeId: node.id,
        projection: projection(runInput, node, cid, causes)
      });
    }
    case 'think':
      return await activities.invokeBrain({
        cid,
        brain: node.step.brain,
        model: node.step.model,
        modelSettings: node.step.modelSettings,
        ctx: node.step.ctx ?? { kind: 'input_only' },
        input: value,
        sessionId: runInput.sessionId,
        nodeId: node.id,
        projection: projection(runInput, node, cid, causes)
      });
    case 'sub': {
      return await executeChild<typeof run>(run, {
        workflowId: `${runInput.sessionId}:${node.step.ref}:${cid}`,
        taskQueue: node.step.contract.taskQueue,
        args: [{ ...runInput, flow: { op: 'app', id: node.step.ref, controller: node.step.ref }, input: value }]
      });
    }
  }
}

async function runApp(node: Node, value: Json, runInput: RunInput, causes: string[]): Promise<Json> {
  const started = Date.now();
  let turn = runInput.appState?.turn ?? 0;
  let v = value;
  const maxTurns = runInput.budget?.maxTurns ?? 50;
  while (turn < maxTurns) {
    const cid = stableCallId(node, { turn, value: v } as Json, runInput.manifestHash);
    const plan = await activities.compilePlan({
      cid,
      controller: required(node.controller, node, 'controller'),
      input: { turn, value: v } as Json,
      grants: runInput.grants ?? {},
      parentManifest: runInput.manifest,
      sessionId: runInput.sessionId,
      nodeId: node.id,
      projection: projection(runInput, node, cid, causes)
    });
    const normalized = normalizePlan(plan, runInput.manifest);
    const mergedManifest = { ...runInput.manifest, ...normalized.manifest };
    v = await evalNode(normalized.flow, v, { ...runInput, manifest: mergedManifest, manifestHash: stableManifestHash(mergedManifest), grants: normalized.grants ?? runInput.grants }, [node.id, `turn:${turn}`]);
    turn += 1;

    if (runInput.budget?.maxWallMs && Date.now() - started > runInput.budget.maxWallMs) break;
    if (workflowInfo().continueAsNewSuggested) {
      return await continueAsNew<typeof run>({ ...runInput, input: v, appState: { turn, value: v } });
    }
  }
  return v;
}

function stableCallId(node: Node, input: Json, manifestHash: string): string {
  const toolHash = node.step?.kind === 'call' ? getStepToolHash(node.step) : undefined;
  return `${node.id}:${manifestHash.slice(0, 12)}:${tinyStableHash({ input, toolHash })}`;
}

function stableManifestHash(manifest: ToolManifest): string {
  return tinyStableHash(Object.keys(manifest).sort());
}

function projection(runInput: RunInput, node: Node, cid: string, causes: string[]): ProjectionEnvelope {
  const info = workflowInfo();
  return { sessionId: runInput.sessionId, workflowId: info.workflowId, runId: info.runId, nodeId: node.id, cid, causes };
}

function flattenPar(node: Node): Node[] {
  if (node.op !== 'par') return [node];
  const left = required(node.left, node, 'left');
  const right = required(node.right, node, 'right');
  if (nodeCombiner(node.ann)) {
    return [left, right].flatMap((b) => b.op === 'par' ? flattenPar(b) : [b]);
  }
  return [...flattenPar(left), ...flattenPar(right)];
}

function required<T>(value: T | undefined, node: Node, field: string): T {
  if (value === undefined) throw new Error(`node ${node.id} (${node.op}) missing ${field}`);
  return value;
}
