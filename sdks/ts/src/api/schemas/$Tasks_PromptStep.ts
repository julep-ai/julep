/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tasks_PromptStep = {
  type: "all-of",
  contains: [
    {
      type: "Tasks_BaseWorkflowStep",
    },
    {
      properties: {
        kind_: {
          type: "Enum",
          isRequired: true,
        },
        prompt: {
          type: "any-of",
          description: `The prompt to run`,
          contains: [
            {
              type: "string",
            },
            {
              type: "array",
              contains: {
                type: "Entries_InputChatMLMessage",
              },
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
    },
  ],
} as const;
