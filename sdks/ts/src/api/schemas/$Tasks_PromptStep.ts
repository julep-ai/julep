/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tasks_PromptStep = {
  type: "all-of",
  contains: [
    {
      properties: {
        kind_: {
          type: "Enum",
          isReadOnly: true,
          isRequired: true,
        },
      },
    },
    {
      properties: {
        kind_: {
          type: "Enum",
          isReadOnly: true,
          isRequired: true,
        },
        prompt: {
          type: "any-of",
          description: `The prompt to run`,
          contains: [
            {
              type: "Common_JinjaTemplate",
            },
          ],
          isRequired: true,
        },
        settings: {
          type: "all-of",
          description: `Settings for the prompt`,
          contains: [
            {
              type: "Chat_ChatSettings",
            },
          ],
        },
      },
    },
  ],
} as const;
