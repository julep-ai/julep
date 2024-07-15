/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Common_identifierSafeUnicode } from "./Common_identifierSafeUnicode";
/**
 * Payload for patching a user
 */
export type Users_PatchUserRequest = {
  metadata?: Record<string, any>;
  /**
   * Name of the user
   */
  name?: Common_identifierSafeUnicode;
  /**
   * About the user
   */
  about?: string;
};
