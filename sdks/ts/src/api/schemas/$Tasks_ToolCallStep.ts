/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tasks_ToolCallStep = {
  properties: {
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
      type: "dictionary",
      contains: {
        properties: {},
      },
      isRequired: true,
    },
  },
} as const;
