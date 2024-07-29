/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * The reason the model stopped generating tokens. This will be `stop`
 * if the model hit a natural stop point or a provided stop sequence,
 * `length` if the maximum number of tokens specified in the request
 * was reached, `content_filter` if content was omitted due to a flag
 * from our content filters, `tool_calls` if the model called a tool.
 */
export type Chat_FinishReason =
  | "stop"
  | "length"
  | "content_filter"
  | "tool_calls";
