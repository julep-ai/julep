/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Executions_UpdateExecutionRequest } from "./Executions_UpdateExecutionRequest";
export type Executions_StopExecutionRequest =
  Executions_UpdateExecutionRequest & {
    status: "cancelled";
    /**
     * The reason for stopping the execution
     */
    reason: string | null;
  };
