/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Common_identifierSafeUnicode } from "./Common_identifierSafeUnicode";
/**
 * Payload for creating a user (and associated documents)
 */
export type Users_CreateUserRequest = {
  metadata?: Record<string, any>;
  /**
   * Name of the user
   */
  name: Common_identifierSafeUnicode;
  /**
   * About the user
   */
  about: string;
  /**
   * Documents to index for this user. (Max: 100 items)
   */
  docs: Array<any>;
};