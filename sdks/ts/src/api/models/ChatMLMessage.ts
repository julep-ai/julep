/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type ChatMLMessage = {
  /**
   * ChatML role (system|assistant|user|function_call)
   */
  role: "user" | "assistant" | "system" | "function_call" | "function";
  /**
   * ChatML content
   */
  content: string;
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
