/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Executions_Transition = {
  properties: {
    type: {
      type: "Enum",
      isReadOnly: true,
      isRequired: true,
    },
    execution_id: {
      type: "all-of",
      contains: [
        {
          type: "Common_uuid",
        },
      ],
      isReadOnly: true,
      isRequired: true,
    },
    output: {
      type: "dictionary",
      contains: {
        properties: {},
      },
      isReadOnly: true,
      isRequired: true,
    },
    current: {
      type: "all-of",
      contains: [
        {
          type: "Executions_TransitionTarget",
        },
      ],
      isReadOnly: true,
      isRequired: true,
    },
    next: {
      type: "all-of",
      contains: [
        {
          type: "Executions_TransitionTarget",
        },
      ],
      isReadOnly: true,
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
  },
} as const;
