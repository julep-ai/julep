/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type Docs_VectorDocSearchRequest = {
  limit: number;
  /**
   * The language to be used for text-only search. Support for other languages coming soon.
   */
  lang: "en-US";
  /**
   * The confidence cutoff level
   */
  confidence: number;
  /**
   * Vector to use in the search. Must be the same dimensions as the embedding model or else an error will be thrown.
   */
  vector: Array<number>;
};
