/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { TransitionType } from "./TransitionType";
export type ExecutionTransition = {
  id: string;
  execution_id: string;
  type: TransitionType;
  from: Array<any>;
  to: Array<any> | null;
  task_token?: string | null;
  /**
   * Outputs from an Execution Transition
   */
  outputs: Record<string, any>;
  /**
   * (Optional) metadata
   */
  metadata?: Record<string, any>;
  created_at: string;
  updated_at?: string;
};
