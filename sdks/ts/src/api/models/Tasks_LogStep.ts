/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Common_PyExpression } from "./Common_PyExpression";
import type { Tasks_BaseWorkflowStep } from "./Tasks_BaseWorkflowStep";
export type Tasks_LogStep = Tasks_BaseWorkflowStep & {
  kind_: "log";
  /**
   * The value to log
   */
  log: Common_PyExpression;
};