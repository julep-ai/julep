/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Chat_GenerationPresetSettings = {
  properties: {
    preset: {
      type: "all-of",
      description: `Generation preset (one of: problem_solving, conversational, fun, prose, creative, business, deterministic, code, multilingual)`,
      contains: [
        {
          type: "Chat_GenerationPreset",
        },
      ],
    },
  },
} as const;
