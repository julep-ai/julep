/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Common_uuid } from "./Common_uuid";
import type { Docs_DocOwner } from "./Docs_DocOwner";
import type { Docs_Snippet } from "./Docs_Snippet";
export type Docs_DocReference = {
  /**
   * The owner of this document.
   */
  owner: Docs_DocOwner;
  /**
   * ID of the document
   */
  readonly id: Common_uuid;
  title?: string;
  snippets: Array<Docs_Snippet>;
  distance: number | null;
};
