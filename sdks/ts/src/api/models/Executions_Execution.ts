/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Common_uuid } from "./Common_uuid";
export type Executions_Execution = {
  /**
   * The ID of the task that the execution is running
   */
  readonly task_id: Common_uuid;
  /**
   * The status of the execution
   */
  readonly status:
    | "queued"
    | "starting"
    | "running"
    | "awaiting_input"
    | "succeeded"
    | "failed"
    | "cancelled";
  /**
   * The input to the execution
   */
  input: Record<string, any>;
  /**
   * The output of the execution
   */
  output?: any;
  /**
   * When this resource was created as UTC date-time
   */
  readonly created_at: string;
  /**
   * When this resource was updated as UTC date-time
   */
  readonly updated_at: string;
  metadata?: Record<string, any>;
  readonly id: Common_uuid;
};
