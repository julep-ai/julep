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
    created_at: {
      type: "string",
      isRequired: true,
      format: "date-time",
    },
    outputs: {
      type: "dictionary",
      contains: {
        properties: {},
      },
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
    type: {
      type: "TransitionType",
      isRequired: true,
    },
  },
} as const;
