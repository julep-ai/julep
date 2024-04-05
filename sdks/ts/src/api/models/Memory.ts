/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type Memory = {
  /**
   * ID of the agent
   */
  agent_id: string;
  /**
   * ID of the user
   */
  user_id: string;
  /**
   * Content of the memory
   */
  content: string;
  /**
   * Memory created at (RFC-3339 format)
   */
  created_at: string;
  /**
   * Memory last accessed at (RFC-3339 format)
   */
  last_accessed_at?: string;
  /**
   * Memory happened at (RFC-3339 format)
   */
  timestamp?: string;
  /**
   * Sentiment (valence) of the memory on a scale of -1 to 1
   */
  sentiment?: number;
  /**
   * Memory id (UUID)
   */
  id: string;
  /**
   * List of entities mentioned in the memory
   */
  entities: Array<any>;
};
