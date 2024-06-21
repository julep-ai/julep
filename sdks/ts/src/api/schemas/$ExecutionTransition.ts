/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $ExecutionTransition = {
  properties: {
    id: {
      type: "string",
      isRequired: true,
      format: "uuid",
    },
    execution_id: {
      type: "string",
      isRequired: true,
      format: "uuid",
    },
    type: {
      type: "TransitionType",
      isRequired: true,
    },
    from: {
      type: "array",
      contains: {
        properties: {},
      },
      isRequired: true,
    },
    to: {
      type: "array",
      contains: {
        properties: {},
      },
      isRequired: true,
      isNullable: true,
    },
    task_token: {
      type: "string",
      isNullable: true,
    },
    outputs: {
      type: "dictionary",
      contains: {
        properties: {},
      },
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
      isRequired: true,
      format: "date-time",
    },
    updated_at: {
      type: "string",
      format: "date-time",
    },
  },
} as const;
