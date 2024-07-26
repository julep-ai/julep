/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Docs_BaseDocSearchRequest = {
  properties: {
    confidence: {
      type: "number",
      description: `The confidence cutoff level`,
      isRequired: true,
      maximum: 1,
    },
    alpha: {
      type: "number",
      description: `The weight to apply to BM25 vs Vector search results. 0 => pure BM25; 1 => pure vector;`,
      isRequired: true,
      maximum: 1,
    },
    mmr: {
      type: "boolean",
      description: `Whether to include the MMR algorithm in the search. Optimizes for diversity in search results.`,
      isRequired: true,
    },
    lang: {
      type: "Enum",
      isRequired: true,
    },
  },
} as const;
