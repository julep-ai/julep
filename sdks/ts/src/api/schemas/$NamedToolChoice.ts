/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $NamedToolChoice = {
  description: `Specifies a tool the model should use. Use to force the model to call a specific function.`,
  properties: {
    type: {
      type: "Enum",
      isRequired: true,
    },
    function: {
      properties: {
        name: {
          type: "string",
          description: `The name of the function to call.`,
          isRequired: true,
        },
      },
      isRequired: true,
    },
  },
} as const;
