/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Executions_CreateExecutionRequest = {
  description: `Payload for creating an execution`,
  properties: {
    input: {
      type: "dictionary",
      contains: {
        properties: {},
      },
      isRequired: true,
    },
    output: {
      description: `The output of the execution if it succeeded`,
      properties: {},
    },
    error: {
      type: "string",
      description: `The error of the execution if it failed`,
    },
    metadata: {
      type: "dictionary",
      contains: {
        properties: {},
      },
    },
  },
} as const;
