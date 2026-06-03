import type {
  CapabilityOverrides,
  CapabilityToolOverride,
  FreezeResult,
  FrozenTool,
  McpSnapshot,
  McpToolSnapshot,
  Node,
  StepCall,
  ToolManifest,
  ToolRef
} from './types.js';
import { cloneJson } from './stable.js';
import { sha256Hex } from './hash.js';
import { conservativeContract, contractFromOverride, defaultContractFromMcpAnnotations } from './tool_contract.js';
import { setStepToolHash } from './util.js';

export class FreezeError extends Error {
  constructor(message: string, readonly path: string) {
    super(`${path}: ${message}`);
    this.name = 'FreezeError';
  }
}

export function freeze(flow: Node, snapshot: McpSnapshot, overrides: CapabilityOverrides = {}): FreezeResult {
  const manifest: ToolManifest = {};
  const frozenFlow = bindNode(flow, snapshot, overrides, manifest, '$');
  const manifestHash = hashManifest(manifest);
  return { flow: frozenFlow, manifest, manifestHash };
}

export function hashManifest(manifest: ToolManifest): string {
  return sha256Hex(Object.values(manifest).sort((a, b) => a.hash.localeCompare(b.hash)));
}

export function toolRefKey(ref: ToolRef): string {
  return ref.kind === 'native' ? ref.name : `${ref.server}/${ref.tool}`;
}

export function toolManifestKey(tool: FrozenTool): string {
  return toolRefKey(tool.ref);
}

export function referencedMcpServers(flow: Node): string[] {
  const out = new Set<string>();
  walk(flow);
  return [...out].sort();

  function walk(n: Node | undefined): void {
    if (!n) return;
    if (n.step?.kind === 'call' && n.step.tool.kind === 'mcp') out.add(n.step.tool.server);
    walk(n.left);
    walk(n.right);
    walk(n.body);
    walk(n.plan);
  }
}

function bindNode(
  node: Node,
  snapshot: McpSnapshot,
  overrides: CapabilityOverrides,
  manifest: ToolManifest,
  path: string
): Node {
  const n = cloneJson(node);
  if (n.left) n.left = bindNode(n.left, snapshot, overrides, manifest, `${path}.left`);
  if (n.right) n.right = bindNode(n.right, snapshot, overrides, manifest, `${path}.right`);
  if (n.body) n.body = bindNode(n.body, snapshot, overrides, manifest, `${path}.body`);
  if (n.plan) n.plan = bindNode(n.plan, snapshot, overrides, manifest, `${path}.plan`);

  if (n.op === 'prim' && n.step?.kind === 'call') {
    const tool = resolveTool(n.step.tool, snapshot, overrides, path);
    manifest[tool.hash] = tool;
    n.step = setStepToolHash(n.step satisfies StepCall, tool.hash);
    n.inputSchema = n.inputSchema ?? n.ann?.inputSchema ?? tool.inputSchema;
    if (!n.outputSchema && !n.ann?.outputSchema && tool.outputSchema) n.outputSchema = tool.outputSchema;
    n.ann = { ...n.ann, effect: tool.contract.effect };
  }
  return n;
}

export function resolveTool(ref: ToolRef, snapshot: McpSnapshot, overrides: CapabilityOverrides = {}, path = '$'): FrozenTool {
  if (ref.kind === 'native') return resolveNative(ref, overrides, path);
  return resolveMcp(ref, snapshot, overrides, path);
}

function resolveNative(ref: Extract<ToolRef, { kind: 'native' }>, overrides: CapabilityOverrides, path: string): FrozenTool {
  const key = ref.name;
  const override = overrides.tools?.[key] ?? overrides.tools?.[`native/${key}`];
  if (!override) throw new FreezeError(`native tool '${ref.name}' requires a capability manifest entry`, path);
  if (override.kind && override.kind !== 'native') throw new FreezeError(`capability entry '${key}' exists but is not kind:native`, path);
  if (!override.endpoint) throw new FreezeError(`native tool '${ref.name}' requires endpoint`, path);

  const inputSchema = override.inputSchema ?? {};
  const outputSchema = override.outputSchema;
  const contract = contractFromOverride(conservativeContract, override);
  const endpoint = override.endpoint;
  const hash = sha256Hex({ kind: 'native', name: ref.name, inputSchema, outputSchema, endpoint, contract });
  return stripUndefined({
    hash,
    ref,
    inputSchema,
    outputSchema,
    contract,
    endpoint,
    dispatch: { kind: 'http' as const, endpoint, auth: override.auth, audience: override.audience }
  });
}

function resolveMcp(ref: Extract<ToolRef, { kind: 'mcp' }>, snapshot: McpSnapshot, overrides: CapabilityOverrides, path: string): FrozenTool {
  const server = snapshot.servers[ref.server];
  if (!server) throw new FreezeError(`missing MCP snapshot for server '${ref.server}'`, path);
  const snapTool = server.tools.find((t) => t.name === ref.tool);
  if (!snapTool) throw new FreezeError(`MCP server '${ref.server}' has no tool '${ref.tool}' in snapshot`, path);

  const key = `${ref.server}/${ref.tool}`;
  const override = overrides.tools?.[key] ?? findMcpOverride(overrides, ref.server, ref.tool);
  if (override && override.kind && override.kind !== 'mcp') throw new FreezeError(`capability entry '${key}' exists but is not kind:mcp`, path);

  const inputSchema = override?.inputSchema ?? snapTool.inputSchema ?? {};
  const outputSchema = override?.outputSchema ?? snapTool.outputSchema;
  const base = defaultContractFromMcpAnnotations(snapTool.annotations);
  const contract = contractFromOverride(base, override);
  const version = server.serverVersion ?? server.version ?? snapTool.version;
  const hash = sha256Hex({ kind: 'mcp', server: ref.server, name: ref.tool, inputSchema, outputSchema, version, contract });
  return stripUndefined({
    hash,
    ref,
    inputSchema,
    outputSchema,
    contract,
    serverVersion: version,
    description: snapTool.description,
    annotations: snapTool.annotations,
    dispatch: { kind: 'mcp' as const, serverUrl: server.url }
  });
}

function findMcpOverride(overrides: CapabilityOverrides, server: string, tool: string): CapabilityToolOverride | undefined {
  return Object.values(overrides.tools ?? {}).find((v) => v.kind === 'mcp' && v.server === server && (v.tool === tool || v.name === tool));
}

export function snapshotFromMcpTools(server: string, tools: McpToolSnapshot[], url?: string, serverVersion?: string): McpSnapshot {
  return { servers: { [server]: stripUndefined({ server, url, serverVersion, tools }) } };
}

function stripUndefined<T extends Record<string, unknown>>(obj: T): T {
  for (const key of Object.keys(obj)) {
    if (obj[key] === undefined) delete obj[key];
  }
  return obj;
}
