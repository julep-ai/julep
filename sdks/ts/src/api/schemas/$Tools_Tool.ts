/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tools_Tool = {
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
    created_at: {
      type: "string",
      description: `When this resource was created as UTC date-time`,
      isReadOnly: true,
      isRequired: true,
      format: "date-time",
    },
    updated_at: {
      type: "string",
      description: `When this resource was updated as UTC date-time`,
      isReadOnly: true,
      isRequired: true,
      format: "date-time",
    },
    id: {
      type: "all-of",
      contains: [
        {
          type: "Common_uuid",
        },
      ],
      isReadOnly: true,
      isRequired: true,
    },
  },
} as const;
