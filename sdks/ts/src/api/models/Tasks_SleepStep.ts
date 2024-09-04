/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Tasks_SleepFor } from "./Tasks_SleepFor";
export type Tasks_SleepStep = {
  /**
   * The kind of step
   */
  readonly kind_: "sleep";
} & {
  readonly kind_: "sleep";
  /**
   * The duration to sleep for (max 31 days)
   */
  sleep: Tasks_SleepFor;
};
