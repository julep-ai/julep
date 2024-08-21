/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tasks_CaseThen = {
  properties: {
    case: {
      type: "any-of",
      description: `The condition to evaluate`,
      contains: [
        {
          type: "Common_PyExpression",
        },
        {
          type: "Enum",
        },
      ],
      isRequired: true,
    },
    then: {
      type: "any-of",
      description: `The steps to run if the condition is true`,
      contains: [
        {
          type: "Tasks_EvaluateStep",
        },
        {
          type: "Tasks_ToolCallStep",
        },
        {
          type: "Tasks_PromptStep",
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
          type: "Tasks_ReturnStep",
        },
        {
          type: "Tasks_SleepStep",
        },
        {
          type: "Tasks_ErrorWorkflowStep",
        },
        {
          type: "Tasks_YieldStep",
        },
        {
          type: "Tasks_WaitForInputStep",
        },
      ],
      isRequired: true,
    },
  },
} as const;
