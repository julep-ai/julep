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
            type: "any-of",
            contains: [
              {
                type: "Chat_SingleChatOutput",
              },
              {
                type: "Chat_MultipleChatOutput",
              },
            ],
          },
          isRequired: true,
        },
      },
    },
  ],
} as const;
