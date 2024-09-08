/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tools_ChosenIntegrationCall = {
  properties: {
    type: {
      type: "Enum",
      isRequired: true,
    },
    integration: {
      properties: {},
      isRequired: true,
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
  },
} as const;
