import { Client, Connection } from '@temporalio/client';
import type { CapabilityOverrides, FreezeResult, McpSnapshot, Node, PlanGrants } from '@csa/core';
import { freeze, validate, lowerUnsafeParContext } from '@csa/core';
import type { RunInput } from './types.js';
import { run } from './workflows/run.js';

export interface DeployOptions {
  temporalAddress?: string;
  namespace?: string;
  taskQueue: string;
  sessionIdPrefix?: string;
  freezeAt?: 'deploy' | 'run';
  grants?: PlanGrants;
  start?: boolean;
}

export interface Deployment {
  frozen: FreezeResult;
  diagnostics: ReturnType<typeof validate>;
  start(input?: unknown, workflowId?: string): Promise<{ workflowId: string; result: Promise<unknown> }>;
  startInput(input?: unknown, workflowId?: string): RunInput;
}

export async function deploy(
  flow: Node,
  snapshot: McpSnapshot,
  overrides: CapabilityOverrides,
  options: DeployOptions
): Promise<Deployment> {
  const frozen0 = freeze(flow, snapshot, overrides);
  const lowered = lowerUnsafeParContext(frozen0.flow);
  const frozen = { ...frozen0, flow: lowered.flow };
  const diagnostics = [
    ...validate(frozen.flow, { manifest: frozen.manifest, checkRaceAdmission: true }),
    ...lowered.events.map((e) => ({
      severity: 'warning' as const,
      code: e.code,
      message: e.reason,
      path: '$',
      nodeId: e.nodeId
    }))
  ];
  const errors = diagnostics.filter((d) => d.severity === 'error');
  if (errors.length > 0) throw new Error(errors.map((e) => `${e.code}: ${e.message}`).join('\n'));

  const makeStartInput = (input?: unknown, workflowId?: string): RunInput => {
    const id = workflowId ?? `${options.sessionIdPrefix ?? 'csa'}-${Date.now()}`;
    return { flow: frozen.flow, manifest: frozen.manifest, manifestHash: frozen.manifestHash, sessionId: id, input: (input ?? null) as never, grants: options.grants };
  };

  return {
    frozen,
    diagnostics,
    startInput: makeStartInput,
    async start(input?: unknown, workflowId?: string) {
      const connection = options.temporalAddress ? await Connection.connect({ address: options.temporalAddress }) : undefined;
      const client = new Client({ connection, namespace: options.namespace });
      const startInput = makeStartInput(input, workflowId);
      const handle = await client.workflow.start(run, {
        taskQueue: options.taskQueue,
        workflowId: startInput.sessionId,
        args: [startInput]
      });
      return { workflowId: startInput.sessionId, result: handle.result() };
    }
  };
}
