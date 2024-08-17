/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tasks_SleepStep = {
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
        sleep: {
          type: "all-of",
          description: `The duration to sleep for`,
          contains: [
            {
              type: "Tasks_SleepFor",
            },
          ],
          isRequired: true,
        },
      },
    },
  ],
} as const;
