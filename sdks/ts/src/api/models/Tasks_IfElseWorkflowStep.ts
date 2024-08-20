/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Common_PyExpression } from "./Common_PyExpression";
import type { Tasks_BaseWorkflowStep } from "./Tasks_BaseWorkflowStep";
import type { Tasks_EmbedStep } from "./Tasks_EmbedStep";
import type { Tasks_ErrorWorkflowStep } from "./Tasks_ErrorWorkflowStep";
import type { Tasks_EvaluateStep } from "./Tasks_EvaluateStep";
import type { Tasks_GetStep } from "./Tasks_GetStep";
import type { Tasks_LogStep } from "./Tasks_LogStep";
import type { Tasks_PromptStep } from "./Tasks_PromptStep";
import type { Tasks_ReturnStep } from "./Tasks_ReturnStep";
import type { Tasks_SearchStep } from "./Tasks_SearchStep";
import type { Tasks_SetStep } from "./Tasks_SetStep";
import type { Tasks_SleepStep } from "./Tasks_SleepStep";
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
    | Tasks_EvaluateStep
    | Tasks_ToolCallStep
    | Tasks_YieldStep
    | Tasks_PromptStep
    | Tasks_ErrorWorkflowStep
    | Tasks_SleepStep
    | Tasks_ReturnStep
    | Tasks_GetStep
    | Tasks_SetStep
    | Tasks_LogStep
    | Tasks_EmbedStep
    | Tasks_SearchStep
    | Tasks_WaitForInputStep;
  /**
   * The steps to run if the condition is false
   */
  else:
    | Tasks_EvaluateStep
    | Tasks_ToolCallStep
    | Tasks_YieldStep
    | Tasks_PromptStep
    | Tasks_ErrorWorkflowStep
    | Tasks_SleepStep
    | Tasks_ReturnStep
    | Tasks_GetStep
    | Tasks_SetStep
    | Tasks_LogStep
    | Tasks_EmbedStep
    | Tasks_SearchStep
    | Tasks_WaitForInputStep;
};
