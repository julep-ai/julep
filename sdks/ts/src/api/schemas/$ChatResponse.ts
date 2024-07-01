/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $ChatResponse = {
  description: `Represents a chat completion response returned by model, based on the provided input.`,
  properties: {
    id: {
      type: "string",
      description: `A unique identifier for the chat completion.`,
      isRequired: true,
      format: "uuid",
    },
    finish_reason: {
      type: "Enum",
      isRequired: true,
    },
    response: {
      type: "array",
      contains: {
        type: "array",
        contains: {
          type: "ChatMLMessage",
        },
      },
      isRequired: true,
    },
    usage: {
      type: "CompletionUsage",
      isRequired: true,
    },
    jobs: {
      type: "array",
      contains: {
        type: "string",
        format: "uuid",
      },
    },
    doc_ids: {
      type: "DocIds",
      isRequired: true,
    },
  },
} as const;
