/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Sessions_ContextOverflowType } from "./Sessions_ContextOverflowType";
/**
 * Payload for updating a session
 */
export type Sessions_UpdateSessionRequest = {
  /**
   * A specific situation that sets the background for this session
   */
  situation: string;
  /**
   * Render system and assistant message content as jinja templates
   */
  render_templates: boolean;
  /**
   * Threshold value for the adaptive context functionality
   */
  token_budget: number | null;
  /**
   * Action to start on context window overflow
   */
  context_overflow: Sessions_ContextOverflowType | null;
  metadata?: Record<string, any>;
};
