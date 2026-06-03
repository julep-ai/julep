import { NativeConnection, Worker } from '@temporalio/worker';
import * as singletonActivities from './activities.js';
import { createActivities } from './activities.js';
import type { RuntimeDeps } from './types.js';

export interface WorkerConfig {
  taskQueue: string;
  address?: string;
  activityDeps?: RuntimeDeps;
}

export async function startWorker(config: WorkerConfig): Promise<void> {
  const connection = await NativeConnection.connect({ address: config.address });
  const worker = await Worker.create({
    connection,
    taskQueue: config.taskQueue,
    workflowsPath: new URL('./workflows/run.js', import.meta.url).pathname,
    activities: config.activityDeps ? createActivities(config.activityDeps) : singletonActivities
  });
  await worker.run();
}
