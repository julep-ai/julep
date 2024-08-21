/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Tasks_CaseThen } from "./Tasks_CaseThen";
export type Tasks_SwitchStep = {
  /**
   * The kind of step
   */
  readonly kind_: "switch";
} & {
  readonly kind_: "switch";
  /**
   * The cond tree
   */
  switch: Array<Tasks_CaseThen>;
};
