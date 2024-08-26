/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Chat_BaseChatOutput } from "./Chat_BaseChatOutput";
import type { Entries_ChatMLMessage } from "./Entries_ChatMLMessage";
/**
 * The output returned by the model. Note that, depending on the model provider, they might return more than one message.
 */
export type Chat_SingleChatOutput = Chat_BaseChatOutput & {
  message: Entries_ChatMLMessage;
};
