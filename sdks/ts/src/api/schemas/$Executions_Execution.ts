/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Executions_Execution = {
  properties: {
    task_id: {
      type: "all-of",
      description: `The ID of the task that the execution is running`,
      contains: [
        {
          type: "Common_uuid",
        },
      ],
      isReadOnly: true,
      isRequired: true,
    },
    status: {
      type: "Enum",
      isReadOnly: true,
      isRequired: true,
    },
    input: {
      type: "dictionary",
      contains: {
        properties: {},
      },
      isRequired: true,
    },
    output: {
      description: `The output of the execution`,
      properties: {},
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
    metadata: {
      type: "dictionary",
      contains: {
        properties: {},
      },
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
  },
} as const;
