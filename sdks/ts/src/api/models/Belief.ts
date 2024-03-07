/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type Belief = {
  /**
   * Type of memory (`belief`)
   */
  type: 'belief';
  /**
   * (Optional) ID of the subject user
   */
  subject?: string;
  /**
   * Content of the memory
   */
  content: string;
  /**
   * Rationale: Why did the model decide to form this memory
   */
  rationale?: string;
  /**
   * Weight (importance) of the memory on a scale of 0-100
   */
  weight: number;
  /**
   * Sentiment (valence) of the memory on a scale of -1 to 1
   */
  sentiment: number;
  /**
   * Belief created at (RFC-3339 format)
   */
  created_at: string;
  /**
   * Belief id (UUID)
   */
  id: string;
};

