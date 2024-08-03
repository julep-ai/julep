/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Sessions_SingleAgentMultiUserSession = {
  type: "all-of",
  contains: [
    {
      type: "Sessions_Session",
    },
    {
      properties: {
        agent: {
          type: "Common_uuid",
          isRequired: true,
        },
        users: {
          type: "array",
          contains: {
            type: "Common_uuid",
          },
          isRequired: true,
        },
      },
    },
  ],
} as const;
