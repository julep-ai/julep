/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Entries_ChatMLRole } from "./Entries_ChatMLRole";
import type { Tools_ChosenToolCall } from "./Tools_ChosenToolCall";
import type { Tools_Tool } from "./Tools_Tool";
import type { Tools_ToolResponse } from "./Tools_ToolResponse";
export type Entries_BaseEntry = {
  role: Entries_ChatMLRole;
  name: string | null;
  content: Tools_Tool | Tools_ChosenToolCall | string | Tools_ToolResponse;
  source:
    | "api_request"
    | "api_response"
    | "tool_response"
    | "internal"
    | "summarizer"
    | "meta";
  tokenizer?: string;
  token_count?: number;
  /**
   * This is the time that this event refers to.
   */
  timestamp: number;
};
