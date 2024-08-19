/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Executions_TransitionTarget = {
  properties: {
    workflow: {
      type: "Common_identifierSafeUnicode",
      isRequired: true,
    },
    step: {
      type: "number",
      isRequired: true,
      format: "uint16",
    },
  },
} as const;
