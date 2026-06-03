import type { CapabilityOverrides, McpSnapshot } from './types.js';
import { brainFromCtx, call, critique, mcpCall, parallel, pipeline, subagent, Contract } from './dsl.js';

export const sampleSnapshot: McpSnapshot = {
  servers: {
    notion: {
      server: 'notion',
      version: '2026-01-01',
      tools: [
        {
          name: 'search',
          inputSchema: { type: 'object', properties: { query: { type: 'string' } }, required: ['query'] },
          outputSchema: { type: 'object', properties: { results: { type: 'array', items: { type: 'object' } } }, required: ['results'] },
          annotations: { readOnlyHint: true, idempotentHint: true, openWorldHint: false }
        }
      ]
    }
  }
};

export const sampleOverrides: CapabilityOverrides = {
  tools: {
    retrieve_docs: {
      kind: 'native',
      endpoint: 'https://retrieve.run.app/invoke',
      effect: 'read',
      idempotency: 'required',
      asserted: true,
      inputSchema: { type: 'object', properties: { query: { type: 'string' } }, required: ['query'] },
      outputSchema: { type: 'object', properties: { docs: { type: 'array', items: { type: 'object' } } }, required: ['docs'] }
    },
    'notion/search': { kind: 'mcp', server: 'notion', effect: 'read', idempotency: 'native', asserted: true }
  }
};

export const sampleFlow = pipeline(
  parallel(call('retrieve_docs'), mcpCall('notion', 'search')),
  critique(3, brainFromCtx('prompts/drafter.ctx/'), { stopPure: 'critiqueConverged' }),
  subagent('reviewer', Contract.agent('result_only'))
);
