/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type Executions_TransitionEvent = {
  readonly type:
    | "init"
    | "init_branch"
    | "finish"
    | "finish_branch"
    | "wait"
    | "resume"
    | "error"
    | "step"
    | "cancelled";
  readonly output: any;
  /**
   * When this resource was created as UTC date-time
   */
  readonly created_at: string;
  /**
   * When this resource was updated as UTC date-time
   */
  readonly updated_at: string;
};
