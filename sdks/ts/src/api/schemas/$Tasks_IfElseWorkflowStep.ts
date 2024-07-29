/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tasks_IfElseWorkflowStep = {
  properties: {
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
      ],
      isRequired: true,
    },
    else: {
      type: "any-of",
      description: `The steps to run if the condition is false`,
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
      ],
      isRequired: true,
    },
  },
} as const;
