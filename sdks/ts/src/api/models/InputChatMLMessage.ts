/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ChatMLImageContentPart } from "./ChatMLImageContentPart";
import type { ChatMLTextContentPart } from "./ChatMLTextContentPart";
export type InputChatMLMessage = {
  /**
   * ChatML role (system|assistant|user|function_call|function|auto)
   */
  role: "user" | "assistant" | "system" | "function_call" | "function" | "auto";
  /**
   * ChatML content
   */
  content:
    | string
    | Array<ChatMLTextContentPart>
    | Array<ChatMLImageContentPart>;
  /**
   * ChatML name
   */
  name?: string;
  /**
   * Whether to continue this message or return a new one
   */
  continue?: boolean;
};
