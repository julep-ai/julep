/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Docs_DocOwner = {
  properties: {
    id: {
      type: "any-of",
      contains: [
        {
          type: "all-of",
          contains: [
            {
              type: "Common_uuid",
            },
          ],
          isReadOnly: true,
        },
        {
          type: "all-of",
          contains: [
            {
              type: "Common_uuid",
            },
          ],
          isReadOnly: true,
        },
      ],
      isRequired: true,
    },
    role: {
      type: "Enum",
      isRequired: true,
    },
  },
} as const;
