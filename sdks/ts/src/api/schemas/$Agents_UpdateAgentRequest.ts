/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Agents_UpdateAgentRequest = {
  description: `Payload for updating a agent`,
  properties: {
    metadata: {
      type: "dictionary",
      contains: {
        properties: {},
      },
    },
    name: {
      type: "all-of",
      description: `Name of the agent`,
      contains: [
        {
          type: "Common_identifierSafeUnicode",
        },
      ],
      isRequired: true,
    },
    about: {
      type: "string",
      description: `About the agent`,
      isRequired: true,
    },
    model: {
      type: "string",
      description: `Model name to use (gpt-4-turbo, gemini-nano etc)`,
      isRequired: true,
    },
    instructions: {
      type: "any-of",
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
      isRequired: true,
    },
    default_settings: {
      type: "any-of",
      description: `Default settings for all sessions created by this agent`,
      contains: [
        {
          type: "Chat_GenerationPresetSettings",
        },
        {
          type: "Chat_OpenAISettings",
        },
        {
          type: "Chat_vLLMSettings",
        },
      ],
    },
  },
} as const;
