/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Common_toolRef = {
  type: "string",
  description: `Naming convention for tool references. Tools are resolved in order: \`step-settings\` -> \`task\` -> \`agent\``,
  pattern: "^(function|integration|system|api_call)\\.(\\w+)$",
} as const;
