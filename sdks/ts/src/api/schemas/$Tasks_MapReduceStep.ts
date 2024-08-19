/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tasks_MapReduceStep = {
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
        map: {
          type: "all-of",
          description: `The steps to run for each iteration`,
          contains: [
            {
              type: "Tasks_MapOver",
            },
          ],
          isRequired: true,
        },
        reduce: {
          type: "all-of",
          description: `The expression to reduce the results (\`_\` is a list of outputs). If not provided, the results are returned as a list.`,
          contains: [
            {
              type: "Common_PyExpression",
            },
          ],
        },
      },
    },
  ],
} as const;
