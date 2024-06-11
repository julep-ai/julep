/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * A valid request payload for creating a session
 */
export type CreateSessionRequest = {
  /**
   * (Optional) User ID of user to associate with this session
   */
  user_id?: string;
  /**
   * Agent ID of agent to associate with this session
   */
  agent_id: string;
  /**
   * A specific situation that sets the background for this session
   */
  situation?: string;
  /**
   * Optional metadata
   */
  metadata?: any;
  /**
   * Render system and assistant message content as jinja templates
   */
  render_templates?: boolean;
  /**
   * Threshold value for the adaptive context functionality
   */
  token_budget?: number;
  /**
   * Action to start on context window overflow
   */
  context_overflow?: string;
};
