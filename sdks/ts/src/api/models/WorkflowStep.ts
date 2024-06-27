/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ErrorWorkflowStep } from "./ErrorWorkflowStep";
import type { EvaluateWorkflowStep } from "./EvaluateWorkflowStep";
import type { IfElseWorkflowStep } from "./IfElseWorkflowStep";
import type { PromptWorkflowStep } from "./PromptWorkflowStep";
import type { ToolCallWorkflowStep } from "./ToolCallWorkflowStep";
import type { YieldWorkflowStep } from "./YieldWorkflowStep";
export type WorkflowStep =
  | PromptWorkflowStep
  | EvaluateWorkflowStep
  | YieldWorkflowStep
  | ToolCallWorkflowStep
  | ErrorWorkflowStep
  | IfElseWorkflowStep;
