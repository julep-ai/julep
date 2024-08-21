/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tasks_SetStep = {
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
