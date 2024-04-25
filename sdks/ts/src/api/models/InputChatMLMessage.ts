/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type InputChatMLMessage = {
  /**
   * ChatML role (system|assistant|user|function_call|function|auto)
   */
  role: "user" | "assistant" | "system" | "function_call" | "function" | "auto";
  /**
   * ChatML content
   */
  content: string;
  /**
   * ChatML name
   */
  name?: string;
  /**
   * Whether to continue this message or return a new one
   */
  continue?: boolean;
};
