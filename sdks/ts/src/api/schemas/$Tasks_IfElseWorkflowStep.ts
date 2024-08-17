/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tasks_IfElseWorkflowStep = {
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
        if: {
          type: "all-of",
          description: `The condition to evaluate`,
          contains: [
            {
              type: "Common_PyExpression",
            },
          ],
          isRequired: true,
        },
        then: {
          type: "any-of",
          description: `The steps to run if the condition is true`,
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
          isRequired: true,
        },
        else: {
          type: "any-of",
          description: `The steps to run if the condition is false`,
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
          isRequired: true,
        },
      },
    },
  ],
} as const;
