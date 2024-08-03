/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type Executions_TaskTokenResumeExecutionRequest = {
  status: "running";
  /**
   * A Task Token is a unique identifier for a specific Task Execution.
   */
  task_token: string;
  /**
   * The input to resume the execution with
   */
  input?: Record<string, any>;
};
