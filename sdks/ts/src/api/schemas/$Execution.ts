/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Execution = {
  properties: {
    id: {
      type: "string",
      isRequired: true,
      format: "uuid",
    },
    task_id: {
      type: "string",
      isRequired: true,
      format: "uuid",
    },
    status: {
      type: "ExecutionStatus",
      isRequired: true,
    },
    arguments: {
      type: "dictionary",
      contains: {
        properties: {},
      },
      isRequired: true,
    },
    user_id: {
      type: "string",
      isNullable: true,
      format: "uuid",
    },
    session_id: {
      type: "string",
      isNullable: true,
      format: "uuid",
    },
    created_at: {
      type: "string",
      isRequired: true,
      format: "date-time",
    },
    updated_at: {
      type: "string",
      isRequired: true,
      format: "date-time",
    },
  },
} as const;
