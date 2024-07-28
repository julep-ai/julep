/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Common_uuid } from "./Common_uuid";
export type Executions_Transition = {
  readonly type: "finish" | "wait" | "error" | "step" | "cancelled";
  readonly execution_id: Common_uuid;
  readonly output: Record<string, any>;
  readonly current: Array<any>;
  readonly next: Array<any> | null;
  readonly id: Common_uuid;
  metadata?: Record<string, any>;
  /**
   * When this resource was created as UTC date-time
   */
  readonly created_at: string;
  /**
   * When this resource was updated as UTC date-time
   */
  readonly updated_at: string;
};
