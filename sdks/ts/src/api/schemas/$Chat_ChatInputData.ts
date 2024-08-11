/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Chat_ChatInputData = {
  properties: {
    messages: {
      type: "array",
      contains: {
        type: "Entries_InputChatMLMessage",
      },
      isRequired: true,
    },
    tools: {
      type: "array",
      contains: {
        type: "Tools_FunctionTool",
      },
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
