/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Docs_DocSearchRequest } from "./Docs_DocSearchRequest";
export type Docs_VectorDocSearchRequest = Docs_DocSearchRequest & {
  vector: Array<number> | Array<Array<number>>;
  /**
   * Vector or vectors to use in the search. Must be the same dimensions as the embedding model or else an error will be thrown.
   */
  vector: Array<number> | Array<Array<number>>;
  mode: "vector";
};
