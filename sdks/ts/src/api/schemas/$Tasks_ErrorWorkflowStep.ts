/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tasks_ErrorWorkflowStep = {
  type: "all-of",
  contains: [
    {
      type: "Tasks_WorkflowStep",
    },
    {
      properties: {
        error: {
          type: "string",
          description: `The error message`,
          isRequired: true,
        },
      },
    },
  ],
} as const;
