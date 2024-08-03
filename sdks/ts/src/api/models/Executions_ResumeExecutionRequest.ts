/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Executions_UpdateExecutionRequest } from "./Executions_UpdateExecutionRequest";
export type Executions_ResumeExecutionRequest =
  Executions_UpdateExecutionRequest & {
    status: "running";
    /**
     * The input to resume the execution with
     */
    input?: Record<string, any>;
  };
