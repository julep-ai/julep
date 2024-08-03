/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Tasks_ErrorWorkflowStep } from "./Tasks_ErrorWorkflowStep";
import type { Tasks_EvaluateStep } from "./Tasks_EvaluateStep";
import type { Tasks_IfElseWorkflowStep } from "./Tasks_IfElseWorkflowStep";
import type { Tasks_PromptStep } from "./Tasks_PromptStep";
import type { Tasks_ToolCallStep } from "./Tasks_ToolCallStep";
import type { Tasks_WaitForInputStep } from "./Tasks_WaitForInputStep";
import type { Tasks_YieldStep } from "./Tasks_YieldStep";
/**
 * Payload for creating a task
 */
export type Tasks_CreateTaskRequest = Record<
  string,
  Array<
    | Tasks_EvaluateStep
    | Tasks_ToolCallStep
    | Tasks_YieldStep
    | Tasks_PromptStep
    | Tasks_ErrorWorkflowStep
    | Tasks_WaitForInputStep
    | Tasks_IfElseWorkflowStep
  >
>;
