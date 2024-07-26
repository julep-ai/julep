/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tools_NamedToolChoice = {
  properties: {
    type: {
      type: "all-of",
      description: `Whether this tool is a \`function\`, \`api_call\`, \`system\` etc. (Only \`function\` tool supported right now)`,
      contains: [
        {
          type: "Tools_ToolType",
        },
      ],
      isRequired: true,
    },
    function: {
      type: "Tools_FunctionCallOption",
    },
    integration: {
      properties: {},
    },
    system: {
      properties: {},
    },
    api_call: {
      properties: {},
    },
  },
} as const;
