/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tasks_ParallelStep = {
  type: "all-of",
  contains: [
    {
      type: "Tasks_BaseWorkflowStep",
    },
    {
      properties: {
        kind_: {
          type: "Enum",
          isRequired: true,
        },
        parallel: {
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
            ],
          },
          isRequired: true,
        },
      },
    },
  ],
} as const;
