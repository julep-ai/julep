/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Common_identifierSafeUnicode } from "./Common_identifierSafeUnicode";
import type { Common_uuid } from "./Common_uuid";
export type Users_User = {
  readonly id: Common_uuid;
  metadata?: Record<string, any>;
  /**
   * When this resource was created as UTC date-time
   */
  readonly created_at: string;
  /**
   * When this resource was updated as UTC date-time
   */
  readonly updated_at: string;
  /**
   * Name of the user
   */
  name: Common_identifierSafeUnicode;
  /**
   * About the user
   */
  about: string;
};
