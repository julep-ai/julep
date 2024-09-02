/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Payload for creating an execution
 */
export type Executions_CreateExecutionRequest = {
  /**
   * The input to the execution
   */
  input: Record<string, any>;
  /**
   * The output of the execution if it succeeded
   */
  output?: any;
  /**
   * The error of the execution if it failed
   */
  error?: string;
  metadata?: Record<string, any>;
};
