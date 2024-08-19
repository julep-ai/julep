/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tasks_SwitchStep = {
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
        switch: {
          type: "array",
          contains: {
            type: "Tasks_CaseThen",
          },
          isRequired: true,
        },
      },
    },
  ],
} as const;
