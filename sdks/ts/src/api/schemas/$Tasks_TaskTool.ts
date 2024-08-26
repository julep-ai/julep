/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tasks_TaskTool = {
  type: "all-of",
  contains: [
    {
      type: "Tools_CreateToolRequest",
    },
    {
      properties: {
        inherited: {
          type: "boolean",
          description: `Read-only: Whether the tool was inherited or not. Only applies within tasks.`,
          isReadOnly: true,
        },
      },
    },
  ],
} as const;
