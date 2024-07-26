/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Common_PyExpression } from "./Common_PyExpression";
import type { Tasks_ErrorWorkflowStep } from "./Tasks_ErrorWorkflowStep";
import type { Tasks_EvaluateStep } from "./Tasks_EvaluateStep";
import type { Tasks_PromptStep } from "./Tasks_PromptStep";
import type { Tasks_ToolCallStep } from "./Tasks_ToolCallStep";
import type { Tasks_YieldStep } from "./Tasks_YieldStep";
export type Tasks_IfElseWorkflowStep = {
  /**
   * The condition to evaluate
   */
  if: Common_PyExpression;
  /**
   * The steps to run if the condition is true
   */
  then:
    | Tasks_EvaluateStep
    | Tasks_ToolCallStep
    | Tasks_YieldStep
    | Tasks_PromptStep
    | Tasks_ErrorWorkflowStep;
  /**
   * The steps to run if the condition is false
   */
  else:
    | Tasks_EvaluateStep
    | Tasks_ToolCallStep
    | Tasks_YieldStep
    | Tasks_PromptStep
    | Tasks_ErrorWorkflowStep;
};
