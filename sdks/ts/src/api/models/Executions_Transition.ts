/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Common_uuid } from "./Common_uuid";
import type { Executions_TransitionEvent } from "./Executions_TransitionEvent";
import type { Executions_TransitionTarget } from "./Executions_TransitionTarget";
export type Executions_Transition = Executions_TransitionEvent & {
  readonly execution_id: Common_uuid;
  readonly current: Executions_TransitionTarget;
  readonly next: Executions_TransitionTarget | null;
  readonly id: Common_uuid;
  metadata?: Record<string, any>;
};
