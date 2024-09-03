/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Chat_ChatInputData = {
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
      isRequired: true,
    },
    tools: {
      type: "array",
      contains: {
        type: "Tools_Tool",
      },
      isRequired: true,
    },
    tool_choice: {
      type: "any-of",
      description: `Can be one of existing tools given to the agent earlier or the ones provided in this request.`,
      contains: [
        {
          type: "Enum",
        },
        {
          type: "Tools_NamedToolChoice",
        },
      ],
    },
  },
} as const;
