/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Common_uuid } from "./Common_uuid";
import type { Docs_DocOwner } from "./Docs_DocOwner";
export type Docs_DocReference = {
  /**
   * The owner of this document.
   */
  owner: Docs_DocOwner;
  /**
   * ID of the document
   */
  readonly id: Common_uuid;
  /**
   * Snippets referred to of the document
   */
  snippet_index: Array<number>;
  title?: string;
  snippet?: string;
};
