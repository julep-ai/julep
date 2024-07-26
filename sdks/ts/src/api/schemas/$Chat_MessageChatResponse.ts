/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Chat_MessageChatResponse = {
  type: "all-of",
  contains: [
    {
      type: "Chat_BaseChatResponse",
    },
    {
      properties: {
        choices: {
          type: "array",
          contains: {
            type: "Chat_ChatOutputChunk",
          },
          isRequired: true,
        },
      },
    },
  ],
} as const;
