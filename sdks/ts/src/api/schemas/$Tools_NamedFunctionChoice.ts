/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tools_NamedFunctionChoice = {
  type: "all-of",
  contains: [
    {
      type: "Tools_NamedToolChoice",
    },
    {
      properties: {
        function: {
          type: "Tools_FunctionCallOption",
          isRequired: true,
        },
        type: {
          type: "Enum",
          isRequired: true,
        },
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
    },
  ],
} as const;
