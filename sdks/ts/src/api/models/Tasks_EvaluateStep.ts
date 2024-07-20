/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Common_PyExpression } from "./Common_PyExpression";
import type { Tasks_WorkflowStep } from "./Tasks_WorkflowStep";
export type Tasks_EvaluateStep = Tasks_WorkflowStep & {
  /**
   * The expression to evaluate
   */
  evaluate: Record<string, Common_PyExpression>;
};
