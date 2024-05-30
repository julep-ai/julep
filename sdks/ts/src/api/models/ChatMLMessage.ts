/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ChatMLImageContentPart } from "./ChatMLImageContentPart";
import type { ChatMLTextContentPart } from "./ChatMLTextContentPart";
export type ChatMLMessage = {
  /**
   * ChatML role (system|assistant|user|function_call|function)
   */
  role: "user" | "assistant" | "system" | "function_call" | "function";
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
   * Message created at (RFC-3339 format)
   */
  created_at: string;
  /**
   * Message ID
   */
  id: string;
};
