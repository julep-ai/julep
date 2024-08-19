/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Common_PyExpression } from "./Common_PyExpression";
import type { Tasks_BaseWorkflowStep } from "./Tasks_BaseWorkflowStep";
export type Tasks_ReturnStep = Tasks_BaseWorkflowStep & {
  kind_: "return";
  /**
   * The value to return
   */
  return: Record<string, Common_PyExpression>;
};
