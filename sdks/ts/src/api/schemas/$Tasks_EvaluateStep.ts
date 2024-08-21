/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tasks_EvaluateStep = {
  type: "all-of",
  contains: [
    {
      properties: {
        kind_: {
          type: "Enum",
          isReadOnly: true,
          isRequired: true,
        },
      },
    },
    {
      properties: {
        kind_: {
          type: "Enum",
          isReadOnly: true,
          isRequired: true,
        },
        evaluate: {
          type: "dictionary",
          contains: {
            type: "Common_PyExpression",
          },
          isRequired: true,
        },
      },
    },
  ],
} as const;
