/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tasks_WaitForInputStep = {
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
        wait_for_input: {
          type: "all-of",
          description: `Any additional info or data`,
          contains: [
            {
              type: "Tasks_WaitForInputInfo",
            },
          ],
          isRequired: true,
        },
      },
    },
  ],
} as const;
