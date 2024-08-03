/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Entries_ChatMLRole } from "./Entries_ChatMLRole";
export type Entries_InputChatMLMessage = {
  /**
   * The role of the message
   */
  role: Entries_ChatMLRole;
  /**
   * The content parts of the message
   */
  content: string | Array<string>;
  /**
   * Name
   */
  name?: string;
  /**
   * Whether to continue this message or return a new one
   */
  continue?: boolean;
};
