/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $CreateTask = {
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
      type: "WorkflowStep",
      description: `Entrypoint Workflow for the Task`,
      isRequired: true,
    },
  },
} as const;
