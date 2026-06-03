import type { FrozenTool, Json, Plan } from '@csa/core';
import { assertPlanValid, hashManifest, normalizePlan } from '@csa/core';
import type { ActivityCallInput, BrainCallInput, CompilePlanInput, NativeRuntime, RuntimeDeps } from './types.js';
import { NoopProjectionWriter } from './projection.js';

let singletonDeps: RuntimeDeps = { projection: new NoopProjectionWriter() };

export function configureActivities(next: RuntimeDeps): void {
  singletonDeps = { ...singletonDeps, ...next };
}

export function createActivities(deps: RuntimeDeps) {
  const runtimeDeps: RuntimeDeps = { projection: new NoopProjectionWriter(), ...deps };
  return {
    callHand: (args: ActivityCallInput) => callHandWithDeps(runtimeDeps, args),
    invokeBrain: (args: BrainCallInput) => invokeBrainWithDeps(runtimeDeps, args),
    compilePlan: (args: CompilePlanInput) => compilePlanWithDeps(runtimeDeps, args)
  };
}

// Singleton exports remain for the simple Worker.create({ activities }) path.
export async function callHand(args: ActivityCallInput): Promise<Json> {
  return callHandWithDeps(singletonDeps, args);
}

export async function invokeBrain(args: BrainCallInput): Promise<Json> {
  return invokeBrainWithDeps(singletonDeps, args);
}

export async function compilePlan(args: CompilePlanInput): Promise<Plan> {
  return compilePlanWithDeps(singletonDeps, args);
}

async function callHandWithDeps(deps: RuntimeDeps, args: ActivityCallInput): Promise<Json> {
  const tool = args.manifest[args.toolHash];
  if (!tool) throw new Error(`Unknown frozen tool hash: ${args.toolHash}`);

  await deps.projection?.planned(args.projection, args.input);
  try {
    const out = tool.ref.kind === 'native'
      ? await callNative(deps.nativeRuntime ?? new FetchNativeRuntime(), tool, args.cid, args.input)
      : await callMcp(deps, tool, args.cid, args.sessionId, args.input);
    await deps.projection?.did(args.projection, out);
    return out;
  } catch (error) {
    await deps.projection?.failed(args.projection, error);
    throw error;
  }
}

async function invokeBrainWithDeps(deps: RuntimeDeps, args: BrainCallInput): Promise<Json> {
  if (!deps.brainRuntime) throw new Error('BrainRuntime not configured.');
  await deps.projection?.planned(args.projection, args.input);
  try {
    const out = await deps.brainRuntime.invoke({
      cid: args.cid,
      brain: args.brain,
      model: args.model,
      modelSettings: args.modelSettings,
      ctx: args.ctx,
      input: args.input,
      sessionId: args.sessionId,
      nodeId: args.nodeId
    });
    await deps.projection?.did(args.projection, out);
    return out;
  } catch (error) {
    await deps.projection?.failed(args.projection, error);
    throw error;
  }
}

async function compilePlanWithDeps(deps: RuntimeDeps, args: CompilePlanInput): Promise<Plan> {
  if (!deps.plannerRuntime) throw new Error('PlannerRuntime not configured.');
  await deps.projection?.planned(args.projection, args.input);
  try {
    const planOrFlow = await deps.plannerRuntime.compile({
      cid: args.cid,
      controller: args.controller,
      input: args.input,
      sessionId: args.sessionId,
      parentManifest: args.parentManifest,
      grants: args.grants
    });
    const plan = normalizePlan(planOrFlow, args.parentManifest);
    const manifest = plan.manifest ?? {};
    const normalized = { ...plan, manifest, manifestHash: plan.manifestHash ?? hashManifest(manifest) };
    assertPlanValid(normalized, args.grants, args.parentManifest, { maxNodes: args.grants.maxNodes ?? 200, maxLoopBound: args.grants.maxLoopBound ?? 20, maxFanout: args.grants.maxFanout ?? 64 });
    await deps.projection?.did(args.projection, { planShape: 'validated', nodeId: normalized.flow.id } as Json);
    return normalized;
  } catch (error) {
    await deps.projection?.failed(args.projection, error);
    throw error;
  }
}

async function callNative(runtime: NativeRuntime, tool: FrozenTool, cid: string, input: Json): Promise<Json> {
  const endpoint = tool.dispatch?.kind === 'http' ? tool.dispatch.endpoint : tool.endpoint;
  if (!endpoint) throw new Error(`Native tool ${label(tool)} has no endpoint.`);
  return runtime.call({ endpoint, cid, input, tool });
}

async function callMcp(deps: RuntimeDeps, tool: FrozenTool, cid: string, sessionId: string, input: Json): Promise<Json> {
  if (!deps.mcpClient) throw new Error('McpRuntime not configured.');
  return await deps.mcpClient.callTool({ cid, sessionId, tool, input });
}

export class FetchNativeRuntime implements NativeRuntime {
  async call(args: { endpoint: string; cid: string; input: Json; headers?: Record<string, string>; tool: FrozenTool }): Promise<Json> {
    const res = await fetch(args.endpoint, {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        'idempotency-key': args.cid,
        ...(args.headers ?? {})
      },
      body: JSON.stringify({ cid: args.cid, input: args.input })
    });
    const text = await res.text();
    const body = text ? safeJson(text) : null;
    if (!res.ok) {
      const detail = typeof body === 'object' ? JSON.stringify(body) : text;
      throw new Error(`Hand HTTP ${res.status} for ${label(args.tool)}: ${detail}`);
    }
    return body as Json;
  }
}

function label(tool: FrozenTool): string {
  return tool.ref.kind === 'native' ? tool.ref.name : `${tool.ref.server}/${tool.ref.tool}`;
}

function safeJson(text: string): unknown {
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}
