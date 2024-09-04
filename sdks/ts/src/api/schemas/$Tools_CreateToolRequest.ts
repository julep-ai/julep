/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tools_CreateToolRequest = {
  description: `Payload for creating a tool`,
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
    name: {
      type: "all-of",
      description: `Name of the tool (must be unique for this agent and a valid python identifier string )`,
      contains: [
        {
          type: "Common_validPythonIdentifier",
        },
      ],
      isRequired: true,
    },
    background: {
      type: "boolean",
      isRequired: true,
    },
    function: {
      type: "all-of",
      description: `The function to call`,
      contains: [
        {
          type: "Tools_FunctionDef",
        },
      ],
      isRequired: true,
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
