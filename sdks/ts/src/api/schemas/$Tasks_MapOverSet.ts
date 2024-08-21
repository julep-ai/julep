/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tasks_MapOverSet = {
  type: "all-of",
  contains: [
    {
      type: "Tasks_SetStepDef",
    },
    {
      properties: {
        over: {
          type: "all-of",
          description: `The variable to iterate over`,
          contains: [
            {
              type: "Common_PyExpression",
            },
          ],
          isRequired: true,
        },
      },
    },
  ],
} as const;
