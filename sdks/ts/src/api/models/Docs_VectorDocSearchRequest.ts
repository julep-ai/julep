/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Docs_BaseDocSearchRequest } from "./Docs_BaseDocSearchRequest";
export type Docs_VectorDocSearchRequest = Docs_BaseDocSearchRequest & {
  /**
   * Vector or vectors to use in the search. Must be the same dimensions as the embedding model or else an error will be thrown.
   */
  vector: Array<number> | Array<Array<number>>;
};
