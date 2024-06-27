/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * A valid request payload for updating a user
 */
export type UpdateUserRequest = {
  /**
   * About the user
   */
  about: string;
  /**
   * Name of the user
   */
  name: string;
  /**
   * Optional metadata
   */
  metadata?: Record<string, any>;
};
