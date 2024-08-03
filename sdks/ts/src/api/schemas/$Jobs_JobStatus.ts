/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Jobs_JobStatus = {
  properties: {
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
    name: {
      type: "all-of",
      description: `Name of the job`,
      contains: [
        {
          type: "Common_identifierSafeUnicode",
        },
      ],
      isRequired: true,
    },
    reason: {
      type: "string",
      description: `Reason for the current state of the job`,
      isRequired: true,
    },
    has_progress: {
      type: "boolean",
      description: `Whether this Job supports progress updates`,
      isRequired: true,
    },
    progress: {
      type: "number",
      description: `Progress percentage`,
      isRequired: true,
      format: "float",
      maximum: 100,
    },
    state: {
      type: "all-of",
      description: `Current state of the job`,
      contains: [
        {
          type: "Jobs_JobState",
        },
      ],
      isRequired: true,
    },
  },
} as const;
