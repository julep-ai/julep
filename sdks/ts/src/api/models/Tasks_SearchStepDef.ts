/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Docs_HybridDocSearchRequest } from "./Docs_HybridDocSearchRequest";
import type { Docs_TextOnlyDocSearchRequest } from "./Docs_TextOnlyDocSearchRequest";
import type { Docs_VectorDocSearchRequest } from "./Docs_VectorDocSearchRequest";
export type Tasks_SearchStepDef = {
  /**
   * The search query
   */
  search:
    | Docs_VectorDocSearchRequest
    | Docs_TextOnlyDocSearchRequest
    | Docs_HybridDocSearchRequest;
};
