/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Chat_CompetionUsage } from "./Chat_CompetionUsage";
import type { Common_uuid } from "./Common_uuid";
import type { Docs_DocReference } from "./Docs_DocReference";
export type Chat_BaseChatResponse = {
  /**
   * Usage statistics for the completion request
   */
  usage: Chat_CompetionUsage | null;
  /**
   * Background job IDs that may have been spawned from this interaction.
   */
  jobs: Array<Common_uuid>;
  /**
   * Documents referenced for this request (for citation purposes).
   */
  docs: Array<Docs_DocReference>;
  /**
   * When this resource was created as UTC date-time
   */
  readonly created_at: string;
  readonly id: Common_uuid;
};
