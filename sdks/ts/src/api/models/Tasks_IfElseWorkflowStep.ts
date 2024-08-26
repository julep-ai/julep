/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Common_PyExpression } from "./Common_PyExpression";
import type { Tasks_BaseWorkflowStep } from "./Tasks_BaseWorkflowStep";
import type { Tasks_ErrorWorkflowStep } from "./Tasks_ErrorWorkflowStep";
import type { Tasks_PromptStep } from "./Tasks_PromptStep";
import type { Tasks_ToolCallStep } from "./Tasks_ToolCallStep";
import type { Tasks_WaitForInputStep } from "./Tasks_WaitForInputStep";
import type { Tasks_YieldStep } from "./Tasks_YieldStep";
export type Tasks_IfElseWorkflowStep = Tasks_BaseWorkflowStep & {
  kind_: "if_else";
  /**
   * The condition to evaluate
   */
  if: Common_PyExpression;
  /**
   * The steps to run if the condition is true
   */
  then:
    | Tasks_ToolCallStep
    | Tasks_YieldStep
    | Tasks_PromptStep
    | Tasks_ErrorWorkflowStep
    | Tasks_WaitForInputStep;
  /**
   * The steps to run if the condition is false
   */
  else:
    | Tasks_ToolCallStep
    | Tasks_YieldStep
    | Tasks_PromptStep
    | Tasks_ErrorWorkflowStep
    | Tasks_WaitForInputStep;
};
