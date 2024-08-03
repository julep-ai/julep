/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Common_identifierSafeUnicode } from "./Common_identifierSafeUnicode";
import type { Common_uuid } from "./Common_uuid";
import type { Jobs_JobState } from "./Jobs_JobState";
export type Jobs_JobStatus = {
  readonly id: Common_uuid;
  /**
   * When this resource was created as UTC date-time
   */
  readonly created_at: string;
  /**
   * When this resource was updated as UTC date-time
   */
  readonly updated_at: string;
  /**
   * Name of the job
   */
  name: Common_identifierSafeUnicode;
  /**
   * Reason for the current state of the job
   */
  reason: string;
  /**
   * Whether this Job supports progress updates
   */
  has_progress: boolean;
  /**
   * Progress percentage
   */
  progress: number;
  /**
   * Current state of the job
   */
  state: Jobs_JobState;
};
