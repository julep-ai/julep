/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Common_uuid } from "./Common_uuid";
import type { Entries_BaseEntry } from "./Entries_BaseEntry";
export type Entries_Entry = Entries_BaseEntry & {
  /**
   * When this resource was created as UTC date-time
   */
  readonly created_at: string;
  readonly id: Common_uuid;
};
