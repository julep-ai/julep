/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tasks_GetStep = {
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
        get: {
          type: "string",
          description: `The key to get`,
          isRequired: true,
        },
      },
    },
  ],
} as const;
