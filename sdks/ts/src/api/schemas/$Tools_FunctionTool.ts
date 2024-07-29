/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tools_FunctionTool = {
  type: "all-of",
  contains: [
    {
      type: "Tools_Tool",
    },
    {
      properties: {
        function: {
          type: "Tools_FunctionDef",
          isRequired: true,
        },
        type: {
          type: "Enum",
          isRequired: true,
        },
        background: {
          type: "boolean",
          isRequired: true,
        },
        function: {
          type: "all-of",
          description: `The function to call`,
          contains: [
            {
              type: "Tools_FunctionDef",
            },
          ],
          isRequired: true,
        },
      },
    },
  ],
} as const;
