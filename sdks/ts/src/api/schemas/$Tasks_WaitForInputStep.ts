/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tasks_WaitForInputStep = {
  type: "all-of",
  contains: [
    {
      type: "Tasks_BaseWorkflowStep",
    },
    {
      properties: {
        kind_: {
          type: "Enum",
          isRequired: true,
        },
        info: {
          type: "any-of",
          description: `Any additional info or data`,
          contains: [
            {
              type: "string",
            },
            {
              type: "dictionary",
              contains: {
                properties: {},
              },
            },
          ],
          isRequired: true,
        },
      },
    },
  ],
} as const;
