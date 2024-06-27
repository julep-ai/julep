/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * A valid request payload for updating a session
 */
export type UpdateSessionRequest = {
  /**
   * Updated situation for this session
   */
  situation: string;
  /**
   * Optional metadata
   */
  metadata?: Record<string, any>;
  /**
   * Threshold value for the adaptive context functionality
   */
  token_budget?: number;
  /**
   * Action to start on context window overflow
   */
  context_overflow?: string;
};
