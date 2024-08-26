/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tasks_ParallelStep = {
  type: "all-of",
  contains: [
    {
      properties: {
        kind_: {
          type: "Enum",
          isReadOnly: true,
          isRequired: true,
        },
      },
    },
    {
      properties: {
        kind_: {
          type: "Enum",
          isReadOnly: true,
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
          },
          isRequired: true,
        },
      },
    },
  ],
} as const;
