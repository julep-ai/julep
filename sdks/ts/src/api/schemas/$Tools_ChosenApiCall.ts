/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tools_ChosenApiCall = {
  properties: {
    type: {
      type: "Enum",
      isRequired: true,
    },
    api_call: {
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
