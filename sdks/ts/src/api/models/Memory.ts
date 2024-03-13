/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type Memory = {
  /**
   * Type of memory (`episode` or `belief`)
   */
  type: "episode" | "belief";
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
   * Weight (importance) of the memory on a scale of 0-100
   */
  weight?: number;
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
   * Duration of the Memory (in seconds)
   */
  duration?: number;
  /**
   * Memory id (UUID)
   */
  id: string;
  emotions?: Array<
    | "admiration"
    | "amusement"
    | "anger"
    | "annoyance"
    | "approval"
    | "caring"
    | "confusion"
    | "curiosity"
    | "desire"
    | "disappointment"
    | "disapproval"
    | "disgust"
    | "embarrassment"
    | "excitement"
    | "fear"
    | "gratitude"
    | "grief"
    | "joy"
    | "love"
    | "nervousness"
    | "neutral"
    | "optimism"
    | "pride"
    | "realization"
    | "relief"
    | "remorse"
    | "sadness"
    | "sarcasm"
    | "surprise"
  >;
};
