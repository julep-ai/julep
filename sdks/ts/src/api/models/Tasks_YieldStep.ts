/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Tasks_CEL } from "./Tasks_CEL";
import type { Tasks_WorkflowStep } from "./Tasks_WorkflowStep";
export type Tasks_YieldStep = Tasks_WorkflowStep & {
  /**
   * The subworkflow to run
   */
  workflow: string;
  /**
   * The input parameters for the subworkflow
   */
  arguments: Record<string, Tasks_CEL>;
};
