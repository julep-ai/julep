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
          type: "all-of",
          contains: [
            {
              properties: {
                kind_: {
                  type: "string",
                  description: `Discriminator property for BaseWorkflowStep.`,
                },
              },
            },
            {
              properties: {
                over: {
                  type: "all-of",
                  description: `The variable to iterate over`,
                  contains: [
                    {
                      type: "Common_PyExpression",
                    },
                  ],
                  isRequired: true,
                },
                map: {
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
                reduce: {
                  type: "all-of",
                  description: `The expression to reduce the results.
              If not provided, the results are collected and returned as a list.
              A special parameter named \`results\` is the accumulator and \`_\` is the current value.`,
                  contains: [
                    {
                      type: "Common_PyExpression",
                    },
                  ],
                },
                initial: {
                  description: `The initial value of the reduce expression`,
                  properties: {},
                },
                parallel: {
                  type: "boolean",
                  description: `Whether to run the reduce expression in parallel`,
                },
              },
            },
          ],
        },
      ],
    },
  },
} as const;
