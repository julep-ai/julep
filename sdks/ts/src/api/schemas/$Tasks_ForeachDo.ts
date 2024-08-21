/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tasks_ForeachDo = {
  properties: {
    in: {
      type: "all-of",
      description: `The variable to iterate over.
      VALIDATION: Should NOT return more than 1000 elements.`,
      contains: [
        {
          type: "Common_PyExpression",
        },
      ],
      isRequired: true,
    },
    do: {
      type: "any-of",
      description: `The steps to run for each iteration`,
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
      ],
      isRequired: true,
    },
  },
} as const;
