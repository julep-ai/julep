/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Chat_BaseChatOutput } from "./Chat_BaseChatOutput";
import type { Entries_ChatMLRole } from "./Entries_ChatMLRole";
/**
 * The output returned by the model. Note that, depending on the model provider, they might return more than one message.
 */
export type Chat_MultipleChatOutput = Chat_BaseChatOutput & {
  messages: Array<{
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
  }>;
};
