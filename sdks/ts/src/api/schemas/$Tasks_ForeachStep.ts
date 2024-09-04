/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tasks_ForeachStep = {
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
        foreach: {
          type: "all-of",
          description: `The steps to run for each iteration`,
          contains: [
            {
              type: "Tasks_ForeachDo",
            },
          ],
          isRequired: true,
        },
      },
    },
  ],
} as const;
