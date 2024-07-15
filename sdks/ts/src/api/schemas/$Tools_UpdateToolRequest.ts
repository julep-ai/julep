/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tools_UpdateToolRequest = {
  description: `Payload for updating a tool`,
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
    background: {
      type: "boolean",
      description: `The tool should be run in the background (not supported at the moment)`,
      isRequired: true,
    },
    interactive: {
      type: "boolean",
      description: `Whether the tool that can be run interactively (response should contain "stop" boolean field)`,
      isRequired: true,
    },
    function: {
      type: "Tools_FunctionDef",
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
