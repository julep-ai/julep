/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type Session = {
  /**
   * Session id (UUID)
   */
  id: string;
  /**
   * User ID of user associated with this session
   */
  user_id?: string;
  /**
   * Agent ID of agent associated with this session
   */
  agent_id: string;
  /**
   * A specific situation that sets the background for this session
   */
  situation?: string;
  /**
   * (null at the beginning) - generated automatically after every interaction
   */
  summary?: string;
  /**
   * Session created at (RFC-3339 format)
   */
  created_at?: string;
  /**
   * Session updated at (RFC-3339 format)
   */
  updated_at?: string;
  /**
   * Optional metadata
   */
  metadata?: any;
  /**
   * Render system and assistant message content as jinja templates
   */
  render_templates?: boolean;
};
