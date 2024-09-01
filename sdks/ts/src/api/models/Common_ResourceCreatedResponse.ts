/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Common_uuid } from "./Common_uuid";
export type Common_ResourceCreatedResponse = {
  /**
   * ID of created resource
   */
  id: Common_uuid;
  /**
   * When this resource was created as UTC date-time
   */
  readonly created_at: string;
  /**
   * IDs (if any) of jobs created as part of this request
   */
  readonly jobs: Array<Common_uuid>;
};
