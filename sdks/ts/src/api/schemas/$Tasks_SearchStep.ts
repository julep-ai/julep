/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tasks_SearchStep = {
  type: "all-of",
  contains: [
    {
      type: "Tasks_BaseWorkflowStep",
    },
    {
      properties: {
        kind_: {
          type: "Enum",
          isRequired: true,
        },
        search: {
          type: "any-of",
          description: `The search query`,
          contains: [
            {
              type: "Docs_VectorDocSearchRequest",
            },
            {
              type: "Docs_TextOnlyDocSearchRequest",
            },
            {
              type: "Docs_HybridDocSearchRequest",
            },
          ],
          isRequired: true,
        },
      },
    },
  ],
} as const;
