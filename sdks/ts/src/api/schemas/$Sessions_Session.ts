/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Sessions_Session = {
  properties: {
    situation: {
      type: "string",
      description: `A specific situation that sets the background for this session`,
      isRequired: true,
    },
    summary: {
      type: "string",
      description: `Summary (null at the beginning) - generated automatically after every interaction`,
      isReadOnly: true,
      isRequired: true,
      isNullable: true,
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
    id: {
      type: "all-of",
      contains: [
        {
          type: "Common_uuid",
        },
      ],
      isReadOnly: true,
      isRequired: true,
    },
    metadata: {
      type: "dictionary",
      contains: {
        properties: {},
      },
    },
    created_at: {
      type: "string",
      description: `When this resource was created as UTC date-time`,
      isReadOnly: true,
      isRequired: true,
      format: "date-time",
    },
    updated_at: {
      type: "string",
      description: `When this resource was updated as UTC date-time`,
      isReadOnly: true,
      isRequired: true,
      format: "date-time",
    },
    kind: {
      type: "string",
      description: `Discriminator property for Session.`,
    },
  },
} as const;
