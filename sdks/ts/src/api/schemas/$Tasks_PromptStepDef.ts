/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tasks_PromptStepDef = {
  properties: {
    prompt: {
      type: "any-of",
      description: `The prompt to run`,
      contains: [
        {
          type: "Common_JinjaTemplate",
        },
      ],
      isRequired: true,
    },
    settings: {
      type: "all-of",
      description: `Settings for the prompt`,
      contains: [
        {
          type: "Chat_ChatSettings",
        },
      ],
      isRequired: true,
    },
  },
} as const;
