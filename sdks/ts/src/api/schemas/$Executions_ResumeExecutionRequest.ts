/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Executions_ResumeExecutionRequest = {
  type: "all-of",
  contains: [
    {
      type: "Executions_UpdateExecutionRequest",
    },
    {
      properties: {
        status: {
          type: "Enum",
          isRequired: true,
        },
        input: {
          type: "dictionary",
          contains: {
            properties: {},
          },
        },
      },
    },
  ],
} as const;
