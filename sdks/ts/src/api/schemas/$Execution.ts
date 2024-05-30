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
    created_at: {
      type: "string",
      isRequired: true,
      format: "uuid",
    },
    arguments: {
      type: "dictionary",
      contains: {
        properties: {},
      },
      isRequired: true,
    },
    status: {
      type: "ExecutionStatus",
      isRequired: true,
    },
  },
} as const;
