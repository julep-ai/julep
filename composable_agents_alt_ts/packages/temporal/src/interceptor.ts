import type { ActivityInput, Next, WorkflowOutboundCallsInterceptor } from '@temporalio/workflow';

// Production note: workflow interceptors run in the workflow sandbox. Keep them deterministic.
// Use them to derive lightweight schedule metadata. Heavy writes should happen in activities or via a history tailer.
export class PomsetWorkflowOutboundInterceptor implements WorkflowOutboundCallsInterceptor {
  async scheduleActivity(input: ActivityInput, next: Next<WorkflowOutboundCallsInterceptor, 'scheduleActivity'>): Promise<unknown> {
    // The activity implementation itself writes Planned/Did/Failed in this scaffold.
    // This hook is where you would attach schedule metadata or enrich headers for a projection activity.
    return await next(input);
  }
}

export const interceptors = () => ({
  outbound: new PomsetWorkflowOutboundInterceptor()
});
