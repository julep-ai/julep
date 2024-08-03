/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Common_uuid } from "./Common_uuid";
import type { Entries_BaseEntry } from "./Entries_BaseEntry";
import type { Entries_Relation } from "./Entries_Relation";
export type Entries_History = {
  entries: Array<Entries_BaseEntry>;
  relations: Array<Entries_Relation>;
  readonly session_id: Common_uuid;
  /**
   * When this resource was created as UTC date-time
   */
  readonly created_at: string;
};
