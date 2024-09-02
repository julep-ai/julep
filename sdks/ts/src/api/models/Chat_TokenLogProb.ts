/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Chat_BaseTokenLogProb } from "./Chat_BaseTokenLogProb";
export type Chat_TokenLogProb = Chat_BaseTokenLogProb & {
  /**
   * The log probabilities of the tokens
   */
  readonly top_logprobs: Array<Chat_BaseTokenLogProb>;
};
