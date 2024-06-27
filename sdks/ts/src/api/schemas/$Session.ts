/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Session = {
  properties: {
    id: {
      type: "string",
      description: `Session id (UUID)`,
      isRequired: true,
      format: "uuid",
    },
    user_id: {
      type: "string",
      description: `User ID of user associated with this session`,
      format: "uuid",
    },
    agent_id: {
      type: "string",
      description: `Agent ID of agent associated with this session`,
      isRequired: true,
      format: "uuid",
    },
    situation: {
      type: "string",
      description: `A specific situation that sets the background for this session`,
    },
    summary: {
      type: "string",
      description: `(null at the beginning) - generated automatically after every interaction`,
    },
    created_at: {
      type: "string",
      description: `Session created at (RFC-3339 format)`,
      format: "date-time",
    },
    updated_at: {
      type: "string",
      description: `Session updated at (RFC-3339 format)`,
      format: "date-time",
    },
    metadata: {
      type: "dictionary",
      contains: {
        properties: {},
      },
    },
    render_templates: {
      type: "boolean",
      description: `Render system and assistant message content as jinja templates`,
    },
    token_budget: {
      type: "number",
      description: `Threshold value for the adaptive context functionality`,
    },
    context_overflow: {
      type: "string",
      description: `Action to start on context window overflow`,
    },
  },
} as const;
