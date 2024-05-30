/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Task = {
  description: `Describes a Task`,
  properties: {
    name: {
      type: "string",
      description: `Name of the Task`,
      isRequired: true,
    },
    description: {
      type: "string",
      description: `Optional Description of the Task`,
    },
    tools_available: {
      type: "array",
      contains: {
        type: "string",
        description: `Tool UUID`,
        format: "uuid",
      },
    },
    input_schema: {
      type: "dictionary",
      contains: {
        properties: {},
      },
    },
    main: {
      type: "array",
      contains: {
        type: "WorkflowStep",
      },
      isRequired: true,
    },
    id: {
      type: "string",
      description: `ID of the Task`,
      isRequired: true,
      format: "uuid",
    },
    created_at: {
      type: "string",
      isRequired: true,
      format: "date-time",
    },
    agent_id: {
      type: "string",
      isRequired: true,
      format: "uuid",
    },
  },
} as const;
