/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Specifies a tool the model should use. Use to force the model to call a specific function.
 */
export type NamedToolChoice = {
  /**
   * The type of the tool. Currently, only `function` is supported.
   */
  type: 'function';
  function: {
    /**
     * The name of the function to call.
     */
    name: string;
  };
};

