/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Docs_BaseDocSearchRequest } from "./Docs_BaseDocSearchRequest";
export type Docs_HybridDocSearchRequest = Docs_BaseDocSearchRequest & {
  /**
   * Text to use in the search. In `hybrid` search mode, either `text` or both `text` and `vector` fields are required.
   */
  text: string;
  /**
   * Vector to use in the search. Must be the same dimensions as the embedding model or else an error will be thrown.
   */
  vector: Array<number>;
};
