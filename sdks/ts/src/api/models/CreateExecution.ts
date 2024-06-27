/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ExecutionStatus } from "./ExecutionStatus";
export type CreateExecution = {
  task_id: string;
  /**
   * JSON Schema of parameters
   */
  arguments: Record<string, any>;
  status: ExecutionStatus;
};
