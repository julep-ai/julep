/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Executions_TaskTokenResumeExecutionRequest = {
  properties: {
    status: {
      type: "Enum",
      isRequired: true,
    },
    task_token: {
      type: "string",
      description: `A Task Token is a unique identifier for a specific Task Execution.`,
      isRequired: true,
    },
    input: {
      type: "dictionary",
      contains: {
        properties: {},
      },
    },
  },
} as const;
