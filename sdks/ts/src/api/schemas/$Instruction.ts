/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Instruction = {
  properties: {
    content: {
      type: "string",
      description: `Content of the instruction`,
      isRequired: true,
    },
    important: {
      type: "boolean",
      description: `Whether this instruction should be marked as important (only up to 3 instructions per agent can be marked important)`,
    },
  },
} as const;
