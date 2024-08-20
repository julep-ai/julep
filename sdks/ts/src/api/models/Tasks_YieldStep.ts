/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Common_PyExpression } from "./Common_PyExpression";
import type { Tasks_BaseWorkflowStep } from "./Tasks_BaseWorkflowStep";
export type Tasks_YieldStep = Tasks_BaseWorkflowStep & {
  kind_: "yield";
  /**
   * The subworkflow to run
   */
  workflow: string;
  /**
   * The input parameters for the subworkflow (defaults to last step output)
   */
  arguments: Record<string, Common_PyExpression> | "_";
};
