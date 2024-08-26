/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Common_identifierSafeUnicode } from "./Common_identifierSafeUnicode";
/**
 * Payload for creating a doc
 */
export type Docs_CreateDocRequest = {
  metadata?: Record<string, any>;
  /**
   * Title describing what this document contains
   */
  title: Common_identifierSafeUnicode;
  /**
   * Contents of the document
   */
  content: string | Array<string>;
};
