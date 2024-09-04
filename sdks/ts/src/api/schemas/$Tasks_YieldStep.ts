/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tasks_YieldStep = {
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
        workflow: {
          type: "string",
          description: `The subworkflow to run.
        VALIDATION: Should resolve to a defined subworkflow.`,
          isRequired: true,
        },
        arguments: {
          type: "any-of",
          description: `The input parameters for the subworkflow (defaults to last step output)`,
          contains: [
            {
              type: "dictionary",
              contains: {
                type: "Common_PyExpression",
              },
            },
            {
              type: "Enum",
            },
          ],
          isRequired: true,
        },
      },
    },
  ],
} as const;
