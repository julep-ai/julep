/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Usage statistics for the completion request
 */
export type Chat_CompetionUsage = {
  /**
   * Number of tokens in the generated completion
   */
  readonly completion_tokens: number;
  /**
   * Number of tokens in the prompt
   */
  readonly prompt_tokens: number;
  /**
   * Total number of tokens used in the request (prompt + completion)
   */
  readonly total_tokens: number;
};
