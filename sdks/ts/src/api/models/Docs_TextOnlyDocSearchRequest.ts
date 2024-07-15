/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Docs_DocSearchRequest } from "./Docs_DocSearchRequest";
export type Docs_TextOnlyDocSearchRequest = Docs_DocSearchRequest & {
  text: string | Array<string>;
  /**
   * Text or texts to use in the search. In `text` search mode, only BM25 is used.
   */
  text: string | Array<string>;
  mode: "text";
};
