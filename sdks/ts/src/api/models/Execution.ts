/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ExecutionStatus } from "./ExecutionStatus";
export type Execution = {
  id: string;
  task_id: string;
  created_at: string;
  /**
   * JSON Schema of parameters
   */
  arguments: Record<string, any>;
  status: ExecutionStatus;
};
