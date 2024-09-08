/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type Docs_HybridDocSearchRequest = {
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
   * The weight to apply to BM25 vs Vector search results. 0 => pure BM25; 1 => pure vector;
   */
  alpha: number;
  /**
   * Text to use in the search. In `hybrid` search mode, either `text` or both `text` and `vector` fields are required.
   */
  text: string;
  /**
   * Vector to use in the search. Must be the same dimensions as the embedding model or else an error will be thrown.
   */
  vector: Array<number>;
};
