/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Common_identifierSafeUnicode } from "./Common_identifierSafeUnicode";
import type { Common_validPythonIdentifier } from "./Common_validPythonIdentifier";
/**
 * Function definition
 */
export type Tools_FunctionDefUpdate = {
  /**
   * DO NOT USE: This will be overriden by the tool name. Here only for compatibility reasons.
   */
  name?: Common_validPythonIdentifier;
  /**
   * Description of the function
   */
  description?: Common_identifierSafeUnicode;
  /**
   * The parameters the function accepts
   */
  parameters?: Record<string, any>;
};
