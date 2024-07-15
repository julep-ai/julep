/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tasks_EvaluateStep = {
  type: "all-of",
  contains: [
    {
      type: "Tasks_WorkflowStep",
    },
    {
      properties: {
        evaluate: {
          type: "dictionary",
          contains: {
            type: "Tasks_CEL",
          },
          isRequired: true,
        },
      },
    },
  ],
} as const;
