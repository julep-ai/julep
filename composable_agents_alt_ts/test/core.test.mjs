import test from 'node:test';
import assert from 'node:assert/strict';
import {
  Contract,
  call,
  freeze,
  mcpCall,
  parallel,
  pipeline,
  race,
  schemaSummary,
  stage,
  subagent,
  surfaceShape,
  closedShape,
  validate,
  lowerUnsafeParContext,
  think,
  referencedMcpServers,
  hashManifest
} from '../packages/core/dist/index.js';

const snapshot = {
  servers: {
    notion: {
      server: 'notion',
      serverVersion: '2026-01-01',
      tools: [
        {
          name: 'search',
          inputSchema: { type: 'object', properties: { query: { type: 'string' } }, required: ['query'] },
          outputSchema: { type: 'object', properties: { results: { type: 'array', items: { type: 'object' } } }, required: ['results'] },
          annotations: { readOnlyHint: true, idempotentHint: true }
        }
      ]
    }
  }
};

const overrides = {
  tools: {
    read_docs: {
      kind: 'native',
      endpoint: 'https://read.example/invoke',
      effect: 'read',
      idempotency: 'required',
      asserted: true,
      inputSchema: { type: 'object' },
      outputSchema: { type: 'object', properties: { docs: { type: 'array' } }, required: ['docs'] }
    },
    write_doc: {
      kind: 'native',
      endpoint: 'https://write.example/invoke',
      effect: 'write',
      idempotency: 'none',
      asserted: true,
      inputSchema: { type: 'object' },
      outputSchema: { type: 'object' }
    },
    'notion/search': { kind: 'mcp', server: 'notion', effect: 'read', idempotency: 'native', asserted: true }
  }
};

test('surface shape stays local while closed shape sees subagent contract', () => {
  const flow = pipeline(parallel(call('read_docs'), mcpCall('notion', 'search')), subagent('reviewer', Contract.agent('result_only')));
  assert.equal(surfaceShape(flow), 'Dataflow');
  assert.equal(closedShape(flow), 'Agent');
});

test('freeze binds tool hashes, manifest hash, schemas, and MCP refs', () => {
  const flow = pipeline(call('read_docs'), mcpCall('notion', 'search'));
  const frozen = freeze(flow, snapshot, overrides);
  assert.equal(Object.keys(frozen.manifest).length, 2);
  assert.equal(frozen.manifestHash, hashManifest(frozen.manifest));
  assert.deepEqual(referencedMcpServers(flow), ['notion']);
  assert.ok(frozen.flow.left.step.toolHash);
  assert.equal(frozen.flow.left.step.toolHash, frozen.flow.left.step.frozenHash);
  assert.equal(schemaSummary(frozen.flow.left.outputSchema), 'object{docs}');
});

test('unsafe race is rejected after freeze', () => {
  const flow = race(call('read_docs'), call('write_doc'));
  const frozen = freeze(flow, snapshot, overrides);
  const diags = validate(frozen.flow, { manifest: frozen.manifest, checkRaceAdmission: true });
  assert.ok(diags.some((d) => d.code === 'E_RACE_ADMISSION'));
});

test('read-only race is accepted', () => {
  const flow = race(call('read_docs'), mcpCall('notion', 'search'));
  const frozen = freeze(flow, snapshot, overrides);
  const diags = validate(frozen.flow, { manifest: frozen.manifest, checkRaceAdmission: true });
  assert.equal(diags.filter((d) => d.severity === 'error').length, 0);
});

test('stage supports both static plans and dynamic controllers', () => {
  const staticPlan = stage(parallel(call('read_docs'), mcpCall('notion', 'search')));
  const staticFrozen = freeze(staticPlan, snapshot, overrides);
  assert.equal(validate(staticFrozen.flow, { manifest: staticFrozen.manifest }).filter((d) => d.severity === 'error').length, 0);

  const dynamic = stage('planner:research');
  const dynamicFrozen = freeze(dynamic, snapshot, overrides);
  assert.equal(validate(dynamicFrozen.flow, { manifest: dynamicFrozen.manifest }).filter((d) => d.severity === 'error').length, 0);
});

test('whole-session context in par lowers to seq with provenance', () => {
  const flow = parallel(think('a', { ctx: { kind: 'whole_session' } }), think('b'));
  const lowered = lowerUnsafeParContext(flow);
  assert.equal(lowered.events.length, 1);
  assert.equal(lowered.flow.op, 'seq');
  assert.equal(lowered.flow.ann.degradedFrom, 'par');
});
