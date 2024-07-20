/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Common_uuid } from "./Common_uuid";
export type Common_ResourceUpdatedResponse = {
  /**
   * ID of updated resource
   */
  id: Common_uuid;
  /**
   * When this resource was updated as UTC date-time
   */
  readonly updated_at: string;
  /**
   * IDs (if any) of jobs created as part of this request
   */
  jobs: Array<Common_uuid>;
};
