/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Episode = {
  properties: {
    type: {
      type: "Enum",
      isRequired: true,
    },
    subject: {
      type: "string",
      description: `(Optional) ID of the subject user`,
      format: "uuid",
    },
    content: {
      type: "string",
      description: `Content of the memory`,
      isRequired: true,
    },
    weight: {
      type: "number",
      description: `Weight (importance) of the memory on a scale of 0-100`,
      isRequired: true,
      maximum: 100,
    },
    created_at: {
      type: "string",
      description: `Episode created at (RFC-3339 format)`,
      isRequired: true,
      format: "date-time",
    },
    last_accessed_at: {
      type: "string",
      description: `Episode last accessed at (RFC-3339 format)`,
      isRequired: true,
      format: "date-time",
    },
    happened_at: {
      type: "string",
      description: `Episode happened at (RFC-3339 format)`,
      isRequired: true,
      format: "date-time",
    },
    duration: {
      type: "number",
      description: `Duration of the episode (in seconds)`,
    },
    id: {
      type: "string",
      description: `Episode id (UUID)`,
      isRequired: true,
      format: "uuid",
    },
  },
} as const;
