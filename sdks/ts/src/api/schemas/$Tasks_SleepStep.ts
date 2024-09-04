/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tasks_SleepStep = {
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
        sleep: {
          type: "all-of",
          description: `The duration to sleep for (max 31 days)`,
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
