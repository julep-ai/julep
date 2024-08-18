/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Common_PyExpression } from "./Common_PyExpression";
import type { Tasks_BaseWorkflowStep } from "./Tasks_BaseWorkflowStep";
export type Tasks_WaitForInputStep = Tasks_BaseWorkflowStep & {
  kind_: "wait_for_input";
  /**
   * Any additional info or data
   */
  wait_for_input: Record<string, Common_PyExpression>;
};
