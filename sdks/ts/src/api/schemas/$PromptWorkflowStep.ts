/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $PromptWorkflowStep = {
  properties: {
    prompt: {
      type: "array",
      contains: {
        type: "InputChatMLMessage",
      },
      isRequired: true,
    },
    settings: {
      type: "ChatSettings",
      isRequired: true,
    },
  },
} as const;
