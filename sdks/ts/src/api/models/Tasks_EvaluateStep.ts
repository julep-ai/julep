/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Tasks_CEL } from "./Tasks_CEL";
import type { Tasks_WorkflowStep } from "./Tasks_WorkflowStep";
export type Tasks_EvaluateStep = Tasks_WorkflowStep & {
  /**
   * The expression to evaluate
   */
  evaluate: Record<string, Tasks_CEL>;
};
