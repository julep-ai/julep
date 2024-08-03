/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Common_uuid } from "./Common_uuid";
import type { Sessions_ContextOverflowType } from "./Sessions_ContextOverflowType";
export type Sessions_Session = {
  /**
   * A specific situation that sets the background for this session
   */
  situation: string;
  /**
   * Summary (null at the beginning) - generated automatically after every interaction
   */
  readonly summary: string | null;
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
  readonly id: Common_uuid;
  metadata?: Record<string, any>;
  /**
   * When this resource was created as UTC date-time
   */
  readonly created_at: string;
  /**
   * When this resource was updated as UTC date-time
   */
  readonly updated_at: string;
  /**
   * Discriminator property for Session.
   */
  kind?: string;
};
