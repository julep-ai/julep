/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $CreateAgentRequest = {
  description: `A valid request payload for creating an agent`,
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
    tools: {
      type: "array",
      contains: {
        type: "CreateToolRequest",
      },
    },
    default_settings: {
      type: "AgentDefaultSettings",
      description: `Default model settings to start every session with`,
    },
    model: {
      type: "string",
      description: `Name of the model that the agent is supposed to use`,
    },
    docs: {
      type: "array",
      contains: {
        type: "CreateDoc",
      },
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
