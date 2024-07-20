/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Sessions_PatchSessionRequest = {
  description: `Payload for patching a session`,
  properties: {
    situation: {
      type: "string",
      description: `A specific situation that sets the background for this session`,
    },
    render_templates: {
      type: "boolean",
      description: `Render system and assistant message content as jinja templates`,
    },
    token_budget: {
      type: "number",
      description: `Threshold value for the adaptive context functionality`,
      isNullable: true,
      format: "uint16",
    },
    context_overflow: {
      type: "one-of",
      description: `Action to start on context window overflow`,
      contains: [
        {
          type: "Sessions_ContextOverflowType",
        },
      ],
      isNullable: true,
    },
    metadata: {
      type: "dictionary",
      contains: {
        properties: {},
      },
    },
  },
} as const;
