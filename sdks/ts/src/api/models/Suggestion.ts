/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type Suggestion = {
  /**
   * Suggestion created at (RFC-3339 format)
   */
  created_at?: string;
  /**
   * Whether the suggestion is for the `agent` or a `user`
   */
  target: 'user' | 'agent';
  /**
   * The content of the suggestion
   */
  content: string;
  /**
   * The message that produced it
   */
  message_id: string;
  /**
   * Session this suggestion belongs to
   */
  session_id: string;
};

