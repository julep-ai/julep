/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Common_uuid } from "./Common_uuid";
export type Docs_Doc = {
  readonly id: Common_uuid;
  metadata?: Record<string, any>;
  /**
   * When this resource was created as UTC date-time
   */
  readonly created_at: string;
  /**
   * Title describing what this document contains
   */
  title: string;
  /**
   * Contents of the document
   */
  content: string | Array<string>;
};
