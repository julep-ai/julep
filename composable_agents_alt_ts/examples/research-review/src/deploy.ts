import { deploy } from '@csa/temporal';
import { flow } from './flow.js';
import { capabilities, snapshot } from './capabilities.js';

const deployment = await deploy(flow, snapshot, capabilities, { taskQueue: 'csa-agents', freezeAt: 'deploy' });
console.log(JSON.stringify({ manifestHash: deployment.frozen.manifestHash, diagnostics: deployment.diagnostics }, null, 2));
