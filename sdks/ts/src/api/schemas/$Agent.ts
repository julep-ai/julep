/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Agent = {
  properties: {
    name: {
      type: "string",
      description: `Name of the agent`,
      isRequired: true,
    },
    about: {
      type: "string",
      description: `About the agent`,
    },
    created_at: {
      type: "string",
      description: `Agent created at (RFC-3339 format)`,
      format: "date-time",
    },
    updated_at: {
      type: "string",
      description: `Agent updated at (RFC-3339 format)`,
      format: "date-time",
    },
    id: {
      type: "string",
      description: `Agent id (UUID)`,
      isRequired: true,
      format: "uuid",
    },
    default_settings: {
      type: "AgentDefaultSettings",
      description: `Default settings for all sessions created by this agent`,
    },
    model: {
      type: "string",
      description: `The model to use with this agent`,
      isRequired: true,
    },
    metadata: {
      type: "dictionary",
      contains: {
        properties: {},
      },
    },
    instructions: {
      type: "one-of",
      description: `Instructions for the agent`,
      contains: [
        {
          type: "string",
        },
        {
          type: "array",
          contains: {
            type: "string",
          },
        },
      ],
    },
  },
} as const;
