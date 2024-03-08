/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $FunctionDef = {
  properties: {
    description: {
      type: "string",
      description: `A description of what the function does, used by the model to choose when and how to call the function.`,
    },
    name: {
      type: "string",
      description: `The name of the function to be called. Must be a-z, A-Z, 0-9, or contain underscores and dashes, with a maximum length of 64.`,
      isRequired: true,
    },
    parameters: {
      type: "FunctionParameters",
      description: `Parameters accepeted by this function`,
      isRequired: true,
    },
  },
} as const;
