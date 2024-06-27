/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * A request for patching a user
 */
export type PatchUserRequest = {
  /**
   * About the user
   */
  about?: string;
  /**
   * Name of the user
   */
  name?: string;
  /**
   * Optional metadata
   */
  metadata?: Record<string, any>;
};
