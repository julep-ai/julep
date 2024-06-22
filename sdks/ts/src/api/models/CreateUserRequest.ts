/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CreateDoc } from "./CreateDoc";
/**
 * A valid request payload for creating a user
 */
export type CreateUserRequest = {
  /**
   * Name of the user
   */
  name?: string;
  /**
   * About the user
   */
  about?: string;
  /**
   * List of docs about user
   */
  docs?: Array<CreateDoc>;
  /**
   * (Optional) metadata
   */
  metadata?: Record<string, any>;
};
