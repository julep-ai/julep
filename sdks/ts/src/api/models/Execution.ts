/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ExecutionStatus } from "./ExecutionStatus";
export type Execution = {
  id: string;
  task_id: string;
  status: ExecutionStatus;
  /**
   * JSON of parameters
   */
  arguments: Record<string, any>;
  user_id?: string | null;
  session_id?: string | null;
  created_at: string;
  updated_at: string;
};
