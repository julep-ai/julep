/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tasks_ToolCallStep = {
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
        tool: {
          type: "all-of",
          description: `The tool to run`,
          contains: [
            {
              type: "Common_toolRef",
            },
          ],
          isRequired: true,
        },
        arguments: {
          type: "any-of",
          description: `The input parameters for the tool (defaults to last step output)`,
          contains: [
            {
              type: "dictionary",
              contains: {
                type: "Common_PyExpression",
              },
            },
            {
              type: "Enum",
            },
          ],
          isRequired: true,
        },
      },
    },
  ],
} as const;
