/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type Docs_BaseDocSearchRequest = {
  /**
   * The confidence cutoff level
   */
  confidence: number;
  /**
   * The weight to apply to BM25 vs Vector search results. 0 => pure BM25; 1 => pure vector;
   */
  alpha: number;
  /**
   * Whether to include the MMR algorithm in the search. Optimizes for diversity in search results.
   */
  mmr: boolean;
  /**
   * The language to be used for text-only search. Support for other languages coming soon.
   */
  lang: "en-US";
};
