/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Common_uuid } from "./Common_uuid";
export type Common_ResourceDeletedResponse = {
  /**
   * ID of deleted resource
   */
  id: Common_uuid;
  /**
   * When this resource was deleted as UTC date-time
   */
  readonly deleted_at: string;
  /**
   * IDs (if any) of jobs created as part of this request
   */
  readonly jobs: Array<Common_uuid>;
};
