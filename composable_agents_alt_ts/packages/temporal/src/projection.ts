import type { Json } from '@csa/core';
import { sha256Hex } from '@csa/core';
import type { ProjectionEnvelope, ProjectionWriter } from './types.js';

export type PomsetKind = 'Planned' | 'Did' | 'Failed';

export interface ProjectionEvent {
  kind: PomsetKind;
  eventId: string;
  cid: string;
  sessionId: string;
  workflowId?: string;
  runId?: string;
  nodeId: string;
  causes: string[];
  payloadRef?: string;
  payloadInline?: Json;
  error?: string;
  createdAt: string;
}

export interface ValueRef {
  hash: string;
  uri: string;
  bytes: number;
}

export interface ValueStore {
  put(value: Json): Promise<ValueRef>;
}

export class MemoryValueStore implements ValueStore {
  readonly values = new Map<string, Json>();
  async put(value: Json): Promise<ValueRef> {
    const bytes = Buffer.byteLength(JSON.stringify(value));
    const hash = sha256Hex(value);
    this.values.set(hash, value);
    return { hash, uri: `mem://${hash}`, bytes };
  }
}

export interface EventWriter {
  write(event: ProjectionEvent): Promise<void>;
}

export class NoopProjectionWriter implements ProjectionWriter {
  async planned(): Promise<void> {}
  async did(): Promise<void> {}
  async failed(): Promise<void> {}
}

export class AppendOnlyProjectionSink implements ProjectionWriter {
  constructor(
    private readonly writer: EventWriter,
    private readonly valueStore: ValueStore = new MemoryValueStore(),
    private readonly inlineThresholdBytes = 16_384
  ) {}

  async planned(envelope: ProjectionEnvelope | undefined, input: Json): Promise<void> {
    if (!envelope) return;
    await this.writer.write(eventFromEnvelope('Planned', envelope, await this.payload(input)));
  }

  async did(envelope: ProjectionEnvelope | undefined, output: Json): Promise<void> {
    if (!envelope) return;
    await this.writer.write(eventFromEnvelope('Did', envelope, await this.payload(output)));
  }

  async failed(envelope: ProjectionEnvelope | undefined, error: unknown): Promise<void> {
    if (!envelope) return;
    await this.writer.write(eventFromEnvelope('Failed', envelope, { error: formatError(error) }));
  }

  private async payload(value: Json): Promise<Pick<ProjectionEvent, 'payloadInline' | 'payloadRef'>> {
    const json = JSON.stringify(value);
    if (Buffer.byteLength(json) <= this.inlineThresholdBytes) return { payloadInline: value };
    const ref = await this.valueStore.put(value);
    return { payloadRef: ref.uri };
  }
}

export class MemoryEventWriter implements EventWriter {
  readonly events: ProjectionEvent[] = [];
  async write(event: ProjectionEvent): Promise<void> {
    this.events.push(event);
  }
}

export interface SqlExecutor {
  query(sql: string, params: unknown[]): Promise<unknown>;
}

export class PostgresEventWriter implements EventWriter {
  constructor(private readonly db: SqlExecutor) {}

  async write(e: ProjectionEvent): Promise<void> {
    await this.db.query(
      `insert into pomset_events
       (event_id, kind, cid, session_id, workflow_id, run_id, node_id, causes, payload_ref, payload_inline, error, created_at)
       values ($1,$2,$3,$4,$5,$6,$7,$8::jsonb,$9,$10::jsonb,$11,$12)
       on conflict do nothing`,
      [e.eventId, e.kind, e.cid, e.sessionId, e.workflowId, e.runId, e.nodeId, JSON.stringify(e.causes), e.payloadRef, e.payloadInline === undefined ? null : JSON.stringify(e.payloadInline), e.error, e.createdAt]
    );
  }
}

export function eventFromEnvelope(kind: PomsetKind, envelope: ProjectionEnvelope, fields: Partial<ProjectionEvent> = {}): ProjectionEvent {
  return {
    kind,
    eventId: fields.eventId ?? `${envelope.cid}:${kind}:${Date.now()}`,
    cid: envelope.cid,
    sessionId: envelope.sessionId,
    workflowId: envelope.workflowId,
    runId: envelope.runId,
    nodeId: envelope.nodeId,
    causes: envelope.causes,
    createdAt: new Date().toISOString(),
    ...fields
  };
}

function formatError(error: unknown): string {
  if (error instanceof Error) return `${error.name}: ${error.message}`;
  return String(error);
}
