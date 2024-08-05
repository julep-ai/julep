/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Docs_DocReference } from "./Docs_DocReference";
export type Docs_DocSearchResponse = {
  /**
   * The documents that were found
   */
  docs: Array<Docs_DocReference>;
  /**
   * The time taken to search in seconds
   */
  time: number;
};
