/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Common_uuid } from "./Common_uuid";
import type { Executions_TransitionTarget } from "./Executions_TransitionTarget";
export type Executions_Transition = {
  readonly type:
    | "init"
    | "init_branch"
    | "finish"
    | "finish_branch"
    | "wait"
    | "resume"
    | "error"
    | "step"
    | "cancelled";
  readonly output: any;
  /**
   * When this resource was created as UTC date-time
   */
  readonly created_at: string;
  /**
   * When this resource was updated as UTC date-time
   */
  readonly updated_at: string;
  readonly execution_id: Common_uuid;
  readonly current: Executions_TransitionTarget;
  readonly next: Executions_TransitionTarget | null;
  readonly id: Common_uuid;
  metadata?: Record<string, any>;
};
