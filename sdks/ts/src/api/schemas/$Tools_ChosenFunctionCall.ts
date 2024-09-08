/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tools_ChosenFunctionCall = {
  properties: {
    type: {
      type: "Enum",
      isRequired: true,
    },
    function: {
      type: "all-of",
      description: `The function to call`,
      contains: [
        {
          type: "Tools_FunctionCallOption",
        },
      ],
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
