/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type User = {
  /**
   * Name of the user
   */
  name?: string;
  /**
   * About the user
   */
  about?: string;
  /**
   * User created at (RFC-3339 format)
   */
  created_at?: string;
  /**
   * User updated at (RFC-3339 format)
   */
  updated_at?: string;
  /**
   * User id (UUID)
   */
  id: string;
  /**
   * (Optional) metadata
   */
  metadata?: Record<string, any>;
};
