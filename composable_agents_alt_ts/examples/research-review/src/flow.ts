import { Contract, brainFromCtx, call, critique, mcpCall, parallel, pipeline, subagent } from '@csa/core';

const retrieve = parallel(call('retrieve_docs'), mcpCall('notion', 'search'));
const drafter = brainFromCtx('prompts/drafter.ctx/');
const reviewer = subagent('reviewer', Contract.agent('result_only'));

export const flow = pipeline(retrieve, critique(3, drafter, { stopPure: 'critiqueConverged' }), reviewer);
