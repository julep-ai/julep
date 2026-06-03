import type { McpServerSnapshot, McpSnapshot, McpToolSnapshot, Node } from '@csa/core';
import { referencedMcpServers } from '@csa/core';

export interface McpSnapshotProvider {
  listTools(server: string): Promise<McpServerSnapshot>;
}

export async function collectMcpSnapshot(servers: string[], provider: McpSnapshotProvider): Promise<McpSnapshot> {
  const entries = await Promise.all(servers.map(async (server) => [server, await provider.listTools(server)] as const));
  return { servers: Object.fromEntries(entries) };
}

export async function collectReferencedMcpSnapshot(flow: Node, provider: McpSnapshotProvider): Promise<McpSnapshot> {
  return collectMcpSnapshot(referencedMcpServers(flow), provider);
}

export function normalizeMcpTool(raw: {
  name: string;
  inputSchema?: unknown;
  outputSchema?: unknown;
  annotations?: unknown;
  description?: string;
  version?: string;
}): McpToolSnapshot {
  return {
    name: raw.name,
    inputSchema: isObj(raw.inputSchema) ? raw.inputSchema : {},
    outputSchema: isObj(raw.outputSchema) ? raw.outputSchema : undefined,
    annotations: isObj(raw.annotations) ? raw.annotations : undefined,
    description: raw.description,
    version: raw.version
  } as McpToolSnapshot;
}

function isObj(x: unknown): x is Record<string, unknown> {
  return Boolean(x && typeof x === 'object' && !Array.isArray(x));
}
