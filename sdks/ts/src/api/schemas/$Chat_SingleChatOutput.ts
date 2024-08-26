/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Chat_SingleChatOutput = {
  type: "all-of",
  description: `The output returned by the model. Note that, depending on the model provider, they might return more than one message.`,
  contains: [
    {
      type: "Chat_BaseChatOutput",
    },
    {
      properties: {
        message: {
          type: "Entries_ChatMLMessage",
          isRequired: true,
        },
      },
    },
  ],
} as const;
