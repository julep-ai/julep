/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type Episode = {
  /**
   * Type of memory (`episode`)
   */
  type: "episode";
  /**
   * (Optional) ID of the subject user
   */
  subject?: string;
  /**
   * Content of the memory
   */
  content: string;
  /**
   * Weight (importance) of the memory on a scale of 0-100
   */
  weight: number;
  /**
   * Episode created at (RFC-3339 format)
   */
  created_at: string;
  /**
   * Episode last accessed at (RFC-3339 format)
   */
  last_accessed_at: string;
  /**
   * Episode happened at (RFC-3339 format)
   */
  happened_at: string;
  /**
   * Duration of the episode (in seconds)
   */
  duration?: number;
  /**
   * Episode id (UUID)
   */
  id: string;
};
