/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Chat_FinishReason } from "./Chat_FinishReason";
import type { Chat_LogProbResponse } from "./Chat_LogProbResponse";
export type Chat_BaseChatOutput = {
  index: number;
  /**
   * The reason the model stopped generating tokens
   */
  finish_reason: Chat_FinishReason;
  /**
   * The log probabilities of tokens
   */
  logprobs?: Chat_LogProbResponse;
};
