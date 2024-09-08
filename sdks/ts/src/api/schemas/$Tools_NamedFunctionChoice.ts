/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tools_NamedFunctionChoice = {
  properties: {
    function: {
      type: "all-of",
      description: `The function to call`,
      contains: [
        {
          type: "Tools_FunctionCallOption",
        },
      ],
      isRequired: true,
    },
  },
} as const;
