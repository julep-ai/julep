/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tasks_IfElseWorkflowStep = {
  type: "all-of",
  contains: [
    {
      type: "Tasks_WorkflowStep",
    },
    {
      properties: {
        if: {
          type: "all-of",
          description: `The condition to evaluate`,
          contains: [
            {
              type: "Tasks_CEL",
            },
          ],
          isRequired: true,
        },
        then: {
          type: "all-of",
          description: `The steps to run if the condition is true`,
          contains: [
            {
              type: "Tasks_WorkflowStep",
            },
          ],
          isRequired: true,
        },
        else: {
          type: "all-of",
          description: `The steps to run if the condition is false`,
          contains: [
            {
              type: "Tasks_WorkflowStep",
            },
          ],
          isRequired: true,
        },
      },
    },
  ],
} as const;
