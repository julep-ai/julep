/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $IfElseWorkflowStep = {
  properties: {
    if: {
      type: "string",
      isRequired: true,
    },
    then: {
      type: "YieldWorkflowStep",
      isRequired: true,
    },
    else: {
      type: "YieldWorkflowStep",
      isRequired: true,
    },
  },
} as const;
