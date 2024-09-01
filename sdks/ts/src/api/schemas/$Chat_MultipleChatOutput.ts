/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Chat_MultipleChatOutput = {
  type: "all-of",
  description: `The output returned by the model. Note that, depending on the model provider, they might return more than one message.`,
  contains: [
    {
      type: "Chat_BaseChatOutput",
    },
    {
      properties: {
        messages: {
          type: "array",
          contains: {
            properties: {
              role: {
                type: "all-of",
                description: `The role of the message`,
                contains: [
                  {
                    type: "Entries_ChatMLRole",
                  },
                ],
                isRequired: true,
              },
              content: {
                type: "any-of",
                description: `The content parts of the message`,
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
              name: {
                type: "string",
                description: `Name`,
              },
              continue: {
                type: "boolean",
                description: `Whether to continue this message or return a new one`,
              },
            },
          },
          isReadOnly: true,
          isRequired: true,
        },
      },
    },
  ],
} as const;
