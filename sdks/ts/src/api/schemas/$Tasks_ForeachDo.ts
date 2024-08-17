/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tasks_ForeachDo = {
  properties: {
    in: {
      type: "all-of",
      description: `The variable to iterate over`,
      contains: [
        {
          type: "Common_PyExpression",
        },
      ],
      isRequired: true,
    },
    do: {
      type: "array",
      contains: {
        type: "any-of",
        contains: [
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
} as const;
