/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type JobStatus = {
  /**
   * Name of the job
   */
  name: string;
  /**
   * Reason for current state
   */
  reason?: string;
  /**
   * Job created at (RFC-3339 format)
   */
  created_at: string;
  /**
   * Job updated at (RFC-3339 format)
   */
  updated_at?: string;
  /**
   * Job id (UUID)
   */
  id: string;
  /**
   * Whether this Job supports progress updates
   */
  has_progress?: boolean;
  /**
   * Progress percentage
   */
  progress?: number;
  /**
   * Current state (one of: pending, in_progress, retrying, succeeded, aborted, failed)
   */
  state: 'pending' | 'in_progress' | 'retrying' | 'succeeded' | 'aborted' | 'failed' | 'unknown';
};

