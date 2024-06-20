/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { TransitionType } from "./TransitionType";
export type ExecutionTransition = {
  id: string;
  execution_id: string;
  created_at: string;
  /**
   * Outputs from an Execution Transition
   */
  outputs: Record<string, any>;
  from: Array<any>;
  to: Array<any> | null;
  type: TransitionType;
};
