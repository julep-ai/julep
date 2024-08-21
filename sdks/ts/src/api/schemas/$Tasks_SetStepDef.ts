/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tasks_SetStepDef = {
  properties: {
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
} as const;
