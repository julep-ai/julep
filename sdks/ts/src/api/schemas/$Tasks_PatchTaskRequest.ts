/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tasks_PatchTaskRequest = {
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
          type: "Tasks_SleepStep",
        },
        {
          type: "Tasks_ReturnStep",
        },
        {
          type: "Tasks_GetStep",
        },
        {
          type: "Tasks_SetStep",
        },
        {
          type: "Tasks_LogStep",
        },
        {
          type: "Tasks_EmbedStep",
        },
        {
          type: "Tasks_SearchStep",
        },
        {
          type: "Tasks_WaitForInputStep",
        },
        {
          type: "Tasks_IfElseWorkflowStep",
        },
        {
          type: "Tasks_SwitchStep",
        },
        {
          type: "Tasks_ForeachStep",
        },
        {
          type: "Tasks_ParallelStep",
        },
        {
          type: "Tasks_MapReduceStep",
        },
      ],
    },
  },
} as const;
