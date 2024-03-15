/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $FunctionCallOption = {
  description: `Specifying a particular function via \`{"name": "my_function"}\` forces the model to call that function.
  `,
  properties: {
    name: {
      type: "string",
      description: `The name of the function to call.`,
      isRequired: true,
    },
  },
} as const;
