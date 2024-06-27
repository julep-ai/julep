/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $WorkflowStep = {
  type: "any-of",
  contains: [
    {
      type: "PromptWorkflowStep",
      description: `Workflow Step for the Prompt`,
    },
    {
      type: "EvaluateWorkflowStep",
      description: `Workflow Step for the Evaluate using CEL`,
    },
    {
      type: "YieldWorkflowStep",
      description: `Workflow Step to call another Workflow`,
    },
    {
      type: "ToolCallWorkflowStep",
      description: `Workflow Step for calling a Tool`,
    },
    {
      type: "ErrorWorkflowStep",
      description: `Workflow Step for handling an Error`,
    },
    {
      type: "IfElseWorkflowStep",
      description: `Workflow Step for If, Then, Else`,
    },
  ],
} as const;
