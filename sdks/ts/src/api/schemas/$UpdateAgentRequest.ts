/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $UpdateAgentRequest = {
  description: `A valid request payload for updating an agent`,
  properties: {
    about: {
      type: "string",
      description: `About the agent`,
      isRequired: true,
    },
    name: {
      type: "string",
      description: `Name of the agent`,
      isRequired: true,
    },
    model: {
      type: "string",
      description: `Name of the model that the agent is supposed to use`,
    },
    default_settings: {
      type: "AgentDefaultSettings",
      description: `Default model settings to start every session with`,
    },
    metadata: {
      description: `Optional metadata`,
      properties: {},
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
