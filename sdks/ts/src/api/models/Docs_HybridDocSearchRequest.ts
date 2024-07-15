/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Docs_DocSearchRequest } from "./Docs_DocSearchRequest";
export type Docs_HybridDocSearchRequest = Docs_DocSearchRequest & {
  /**
   * Text or texts to use in the search. In `hybrid` search mode, either `text` or both `text` and `vector` fields are required.
   */
  text?: string | Array<string>;
  /**
   * Vector or vectors to use in the search. Must be the same dimensions as the embedding model or else an error will be thrown.
   */
  vector?: Array<number> | Array<Array<number>>;
  mode: "hybrid";
};
