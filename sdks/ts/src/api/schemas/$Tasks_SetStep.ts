/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tasks_SetStep = {
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
        set: {
          type: "all-of",
          description: `The value to set`,
          contains: [
            {
              type: "Tasks_SetKey",
            },
          ],
          isRequired: true,
        },
      },
    },
  ],
} as const;
