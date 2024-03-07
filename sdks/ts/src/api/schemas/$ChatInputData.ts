/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $ChatInputData = {
  properties: {
    messages: {
      type: 'array',
      contains: {
        type: 'InputChatMLMessage',
      },
      isRequired: true,
    },
    tools: {
      type: 'array',
      contains: {
        type: 'Tool',
      },
      isNullable: true,
    },
    tool_choice: {
      type: 'one-of',
      description: `Can be one of existing tools given to the agent earlier or the ones included in the request`,
      contains: [{
        type: 'ToolChoiceOption',
      }, {
        type: 'NamedToolChoice',
      }],
      isNullable: true,
    },
  },
} as const;
