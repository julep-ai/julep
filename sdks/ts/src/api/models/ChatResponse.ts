/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ChatMLMessage } from "./ChatMLMessage";
import type { CompletionUsage } from "./CompletionUsage";
import type { DocIds } from "./DocIds";
/**
 * Represents a chat completion response returned by model, based on the provided input.
 */
export type ChatResponse = {
  /**
   * A unique identifier for the chat completion.
   */
  id: string;
  /**
   * The reason the model stopped generating tokens. This will be `stop` if the model hit a natural stop point or a provided stop sequence, `length` if the maximum number of tokens specified in the request was reached, `content_filter` if content was omitted due to a flag from our content filters, `tool_calls` if the model called a tool, or `function_call` (deprecated) if the model called a function.
   */
  finish_reason:
    | "stop"
    | "length"
    | "tool_calls"
    | "content_filter"
    | "function_call";
  /**
   * A list of chat completion messages produced as a response.
   */
  response: Array<Array<ChatMLMessage>>;
  usage: CompletionUsage;
  /**
   * IDs (if any) of jobs created as part of this request
   */
  jobs?: Array<string>;
  doc_ids: DocIds;
};
