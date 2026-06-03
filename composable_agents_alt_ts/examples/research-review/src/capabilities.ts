import type { CapabilityOverrides, McpSnapshot } from '@csa/core';

export const capabilities: CapabilityOverrides = {
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
  },
  models: ['anthropic/claude-*'],
  network: { egress: ['*.run.app', '*.lambda-url.*.on.aws'] }
};

export const snapshot: McpSnapshot = {
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
