/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tasks_UpdateTaskRequest = {
  type: "dictionary",
  contains: {
    type: "array",
    contains: {
      type: "any-of",
      contains: [
        {
          type: "Tasks_EvaluateStep",
        },
        {
          type: "Tasks_ToolCallStep",
        },
        {
          type: "Tasks_YieldStep",
        },
        {
          type: "Tasks_PromptStep",
        },
        {
          type: "Tasks_ErrorWorkflowStep",
        },
        {
          type: "Tasks_IfElseWorkflowStep",
        },
      ],
    },
  },
} as const;
