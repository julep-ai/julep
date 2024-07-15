/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Common_identifierSafeUnicode } from "./Common_identifierSafeUnicode";
import type { Common_uuid } from "./Common_uuid";
export type Users_CreateOrUpdateUserRequest = {
  id: Common_uuid;
  metadata?: Record<string, any>;
  /**
   * Name of the user
   */
  name: Common_identifierSafeUnicode;
  /**
   * About the user
   */
  about: string;
};
