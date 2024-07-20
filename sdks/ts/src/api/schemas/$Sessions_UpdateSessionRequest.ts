/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Sessions_UpdateSessionRequest = {
  description: `Payload for updating a session`,
  properties: {
    situation: {
      type: "string",
      description: `A specific situation that sets the background for this session`,
      isRequired: true,
    },
    render_templates: {
      type: "boolean",
      description: `Render system and assistant message content as jinja templates`,
      isRequired: true,
    },
    token_budget: {
      type: "number",
      description: `Threshold value for the adaptive context functionality`,
      isRequired: true,
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
      isRequired: true,
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
