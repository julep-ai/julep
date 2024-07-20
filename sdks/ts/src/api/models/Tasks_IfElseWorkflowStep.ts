/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Common_PyExpression } from "./Common_PyExpression";
import type { Tasks_WorkflowStep } from "./Tasks_WorkflowStep";
export type Tasks_IfElseWorkflowStep = Tasks_WorkflowStep & {
  /**
   * The condition to evaluate
   */
  if: Common_PyExpression;
  /**
   * The steps to run if the condition is true
   */
  then: Tasks_WorkflowStep;
  /**
   * The steps to run if the condition is false
   */
  else: Tasks_WorkflowStep;
};
