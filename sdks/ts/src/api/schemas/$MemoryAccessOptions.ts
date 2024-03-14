/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $MemoryAccessOptions = {
  properties: {
    recall: {
      type: "boolean",
      description: `Whether previous memories should be recalled or not`,
    },
    record: {
      type: "boolean",
      description: `Whether this interaction should be recorded in history or not`,
    },
    remember: {
      type: "boolean",
      description: `Whether this interaction should form memories or not`,
    },
  },
} as const;
