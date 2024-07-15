/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Agents_Agent } from "../models/Agents_Agent";
import type { Agents_CreateAgentRequest } from "../models/Agents_CreateAgentRequest";
import type { Agents_CreateOrUpdateAgentRequest } from "../models/Agents_CreateOrUpdateAgentRequest";
import type { Agents_PatchAgentRequest } from "../models/Agents_PatchAgentRequest";
import type { Agents_UpdateAgentRequest } from "../models/Agents_UpdateAgentRequest";
import type { Common_limit } from "../models/Common_limit";
import type { Common_offset } from "../models/Common_offset";
import type { Common_uuid } from "../models/Common_uuid";
import type { Docs_Doc } from "../models/Docs_Doc";
import type { Docs_DocReference } from "../models/Docs_DocReference";
import type { Docs_DocSearchRequest } from "../models/Docs_DocSearchRequest";
import type { Entries_History } from "../models/Entries_History";
import type { Executions_CreateExecutionRequest } from "../models/Executions_CreateExecutionRequest";
import type { Executions_Execution } from "../models/Executions_Execution";
import type { Executions_TaskTokenResumeExecutionRequest } from "../models/Executions_TaskTokenResumeExecutionRequest";
import type { Executions_Transition } from "../models/Executions_Transition";
import type { Executions_UpdateExecutionRequest } from "../models/Executions_UpdateExecutionRequest";
import type { Jobs_JobStatus } from "../models/Jobs_JobStatus";
import type { Sessions_CreateOrUpdateSessionRequest } from "../models/Sessions_CreateOrUpdateSessionRequest";
import type { Sessions_CreateSessionRequest } from "../models/Sessions_CreateSessionRequest";
import type { Sessions_PatchSessionRequest } from "../models/Sessions_PatchSessionRequest";
import type { Sessions_Session } from "../models/Sessions_Session";
import type { Sessions_UpdateSessionRequest } from "../models/Sessions_UpdateSessionRequest";
import type { Tasks_CreateOrUpdateTaskRequest } from "../models/Tasks_CreateOrUpdateTaskRequest";
import type { Tasks_CreateTaskRequest } from "../models/Tasks_CreateTaskRequest";
import type { Tasks_PatchTaskRequest } from "../models/Tasks_PatchTaskRequest";
import type { Tasks_Task } from "../models/Tasks_Task";
import type { Tasks_UpdateTaskRequest } from "../models/Tasks_UpdateTaskRequest";
import type { Tools_PatchToolRequest } from "../models/Tools_PatchToolRequest";
import type { Tools_Tool } from "../models/Tools_Tool";
import type { Tools_UpdateToolRequest } from "../models/Tools_UpdateToolRequest";
import type { Users_CreateOrUpdateUserRequest } from "../models/Users_CreateOrUpdateUserRequest";
import type { Users_CreateUserRequest } from "../models/Users_CreateUserRequest";
import type { Users_PatchUserRequest } from "../models/Users_PatchUserRequest";
import type { Users_UpdateUserRequest } from "../models/Users_UpdateUserRequest";
import type { Users_User } from "../models/Users_User";
import type { CancelablePromise } from "../core/CancelablePromise";
import type { BaseHttpRequest } from "../core/BaseHttpRequest";
export class DefaultService {
  constructor(public readonly httpRequest: BaseHttpRequest) {}
  /**
   * List undefined items
   * @returns any The request has succeeded.
   * @throws ApiError
   */
  public agentsRouteList({
    limit = 100,
    offset,
    sortBy = "created_at",
    direction = "asc",
    metadataFilter = "{}",
  }: {
    /**
     * Limit the number of undefined items returned
     */
    limit?: Common_limit;
    /**
     * Offset the undefined items returned
     */
    offset: Common_offset;
    /**
     * Sort by a field
     */
    sortBy?: "created_at" | "updated_at" | "deleted_at";
    /**
     * Sort direction
     */
    direction?: "asc" | "desc";
    /**
     * JSON string of object that should be used to filter objects by metadata
     */
    metadataFilter?: string;
  }): CancelablePromise<{
    results: Array<Agents_Agent>;
  }> {
    return this.httpRequest.request({
      method: "GET",
      url: "/agents",
      query: {
        limit: limit,
        offset: offset,
        sort_by: sortBy,
        direction: direction,
        metadata_filter: metadataFilter,
      },
    });
  }
  /**
   * Create new undefined
   * @returns any The request has succeeded and a new resource has been created as a result.
   * @throws ApiError
   */
  public agentsRouteCreate({
    requestBody,
  }: {
    requestBody: Agents_CreateAgentRequest;
  }): CancelablePromise<{
    /**
     * ID of created undefined
     */
    id: Common_uuid;
    /**
     * When this resource was created as UTC date-time
     */
    readonly created_at: string;
    /**
     * IDs (if any) of jobs created as part of this request
     */
    jobs: Array<Common_uuid>;
  }> {
    return this.httpRequest.request({
      method: "POST",
      url: "/agents",
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Create or update undefined (ID is required in payload; existing resource will be overwritten)
   * @returns any The request has succeeded.
   * @throws ApiError
   */
  public agentsRouteCreateOrUpdate({
    requestBody,
  }: {
    requestBody: Agents_CreateOrUpdateAgentRequest;
  }): CancelablePromise<{
    /**
     * ID of updated undefined
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
  }> {
    return this.httpRequest.request({
      method: "PUT",
      url: "/agents",
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Update undefined by id (overwrite)
   * @returns any The request has succeeded.
   * @throws ApiError
   */
  public agentsRouteUpdate({
    id,
    requestBody,
  }: {
    /**
     * ID of the undefined
     */
    id: Common_uuid;
    requestBody: Agents_UpdateAgentRequest;
  }): CancelablePromise<{
    /**
     * ID of updated undefined
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
  }> {
    return this.httpRequest.request({
      method: "PUT",
      url: "/agents/{id}",
      path: {
        id: id,
      },
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Patch undefined by id (merge changes)
   * @returns any The request has succeeded.
   * @throws ApiError
   */
  public agentsRoutePatch({
    id,
    requestBody,
  }: {
    /**
     * ID of the undefined
     */
    id: Common_uuid;
    requestBody: Agents_PatchAgentRequest;
  }): CancelablePromise<{
    /**
     * ID of updated undefined
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
  }> {
    return this.httpRequest.request({
      method: "PATCH",
      url: "/agents/{id}",
      path: {
        id: id,
      },
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Delete undefined by id
   * @returns any The request has been accepted for processing, but processing has not yet completed.
   * @throws ApiError
   */
  public agentsRouteDelete({
    id,
  }: {
    /**
     * ID of the undefined
     */
    id: Common_uuid;
  }): CancelablePromise<{
    /**
     * ID of deleted undefined
     */
    id: Common_uuid;
    /**
     * When this resource was deleted as UTC date-time
     */
    readonly deleted_at: string;
    /**
     * IDs (if any) of jobs created as part of this request
     */
    jobs: Array<Common_uuid>;
  }> {
    return this.httpRequest.request({
      method: "DELETE",
      url: "/agents/{id}",
      path: {
        id: id,
      },
    });
  }
  /**
   * Get undefined by id
   * @returns Agents_Agent The request has succeeded.
   * @throws ApiError
   */
  public agentsRouteGet({
    id,
  }: {
    /**
     * ID of the undefined
     */
    id: Common_uuid;
  }): CancelablePromise<Agents_Agent> {
    return this.httpRequest.request({
      method: "GET",
      url: "/agents/{id}",
      path: {
        id: id,
      },
    });
  }
  /**
   * List undefined items of parent undefined
   * @returns any The request has succeeded.
   * @throws ApiError
   */
  public agentDocsRouteList({
    id,
    limit = 100,
    offset,
    sortBy = "created_at",
    direction = "asc",
    metadataFilter = "{}",
  }: {
    /**
     * ID of parent undefined
     */
    id: Common_uuid;
    /**
     * Limit the number of undefined items returned
     */
    limit?: Common_limit;
    /**
     * Offset the undefined items returned
     */
    offset: Common_offset;
    /**
     * Sort by a field
     */
    sortBy?: "created_at" | "updated_at" | "deleted_at";
    /**
     * Sort direction
     */
    direction?: "asc" | "desc";
    /**
     * JSON string of object that should be used to filter objects by metadata
     */
    metadataFilter?: string;
  }): CancelablePromise<{
    results: Array<Docs_Doc>;
  }> {
    return this.httpRequest.request({
      method: "GET",
      url: "/agents/{id}/docs",
      path: {
        id: id,
      },
      query: {
        limit: limit,
        offset: offset,
        sort_by: sortBy,
        direction: direction,
        metadata_filter: metadataFilter,
      },
    });
  }
  /**
   * Search for documents owned by undefined
   * @returns any The request has succeeded.
   * @throws ApiError
   */
  public agentsDocsSearchRouteSearch({
    id,
    requestBody,
    limit = 100,
    offset,
    sortBy = "created_at",
    direction = "asc",
    metadataFilter = "{}",
  }: {
    /**
     * ID of the undefined
     */
    id: Common_uuid;
    requestBody: {
      body: Docs_DocSearchRequest;
    };
    /**
     * Limit the number of undefined items returned
     */
    limit?: Common_limit;
    /**
     * Offset the undefined items returned
     */
    offset: Common_offset;
    /**
     * Sort by a field
     */
    sortBy?: "created_at" | "updated_at" | "deleted_at";
    /**
     * Sort direction
     */
    direction?: "asc" | "desc";
    /**
     * JSON string of object that should be used to filter objects by metadata
     */
    metadataFilter?: string;
  }): CancelablePromise<{
    results: Array<Docs_DocReference>;
  }> {
    return this.httpRequest.request({
      method: "POST",
      url: "/agents/{id}/search",
      path: {
        id: id,
      },
      query: {
        limit: limit,
        offset: offset,
        sort_by: sortBy,
        direction: direction,
        metadata_filter: metadataFilter,
      },
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * List undefined items of parent undefined
   * @returns any The request has succeeded.
   * @throws ApiError
   */
  public agentToolsRouteList({
    id,
    limit = 100,
    offset,
    sortBy = "created_at",
    direction = "asc",
    metadataFilter = "{}",
  }: {
    /**
     * ID of parent undefined
     */
    id: Common_uuid;
    /**
     * Limit the number of undefined items returned
     */
    limit?: Common_limit;
    /**
     * Offset the undefined items returned
     */
    offset: Common_offset;
    /**
     * Sort by a field
     */
    sortBy?: "created_at" | "updated_at" | "deleted_at";
    /**
     * Sort direction
     */
    direction?: "asc" | "desc";
    /**
     * JSON string of object that should be used to filter objects by metadata
     */
    metadataFilter?: string;
  }): CancelablePromise<{
    results: Array<Tools_Tool>;
  }> {
    return this.httpRequest.request({
      method: "GET",
      url: "/agents/{id}/tools",
      path: {
        id: id,
      },
      query: {
        limit: limit,
        offset: offset,
        sort_by: sortBy,
        direction: direction,
        metadata_filter: metadataFilter,
      },
    });
  }
  /**
   * Create new undefined
   * @returns any The request has succeeded and a new resource has been created as a result.
   * @throws ApiError
   */
  public agentToolsRouteCreate({
    id,
    requestBody,
  }: {
    /**
     * ID of parent undefined
     */
    id: Common_uuid;
    requestBody: Agents_CreateAgentRequest;
  }): CancelablePromise<{
    /**
     * ID of created undefined
     */
    id: Common_uuid;
    /**
     * When this resource was created as UTC date-time
     */
    readonly created_at: string;
    /**
     * IDs (if any) of jobs created as part of this request
     */
    jobs: Array<Common_uuid>;
  }> {
    return this.httpRequest.request({
      method: "POST",
      url: "/agents/{id}/tools",
      path: {
        id: id,
      },
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Get undefined by id
   * @returns Docs_Doc The request has succeeded.
   * @throws ApiError
   */
  public individualDocsRouteGet({
    id,
  }: {
    /**
     * ID of the undefined
     */
    id: Common_uuid;
  }): CancelablePromise<Docs_Doc> {
    return this.httpRequest.request({
      method: "GET",
      url: "/docs/{id}",
      path: {
        id: id,
      },
    });
  }
  /**
   * Delete undefined by id
   * @returns any The request has been accepted for processing, but processing has not yet completed.
   * @throws ApiError
   */
  public individualDocsRouteDelete({
    id,
  }: {
    /**
     * ID of the undefined
     */
    id: Common_uuid;
  }): CancelablePromise<{
    /**
     * ID of deleted undefined
     */
    id: Common_uuid;
    /**
     * When this resource was deleted as UTC date-time
     */
    readonly deleted_at: string;
    /**
     * IDs (if any) of jobs created as part of this request
     */
    jobs: Array<Common_uuid>;
  }> {
    return this.httpRequest.request({
      method: "DELETE",
      url: "/docs/{id}",
      path: {
        id: id,
      },
    });
  }
  /**
   * Update undefined by id (overwrite)
   * @returns any The request has succeeded.
   * @throws ApiError
   */
  public executionsRouteUpdate({
    id,
    requestBody,
  }: {
    /**
     * ID of the undefined
     */
    id: Common_uuid;
    requestBody: Executions_UpdateExecutionRequest;
  }): CancelablePromise<{
    /**
     * ID of updated undefined
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
  }> {
    return this.httpRequest.request({
      method: "PUT",
      url: "/executions/{id}",
      path: {
        id: id,
      },
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Get undefined by id
   * @returns Executions_Execution The request has succeeded.
   * @throws ApiError
   */
  public executionsRouteGet({
    id,
  }: {
    /**
     * ID of the undefined
     */
    id: Common_uuid;
  }): CancelablePromise<Executions_Execution> {
    return this.httpRequest.request({
      method: "GET",
      url: "/executions/{id}",
      path: {
        id: id,
      },
    });
  }
  /**
   * List undefined items of parent undefined
   * @returns any The request has succeeded.
   * @throws ApiError
   */
  public executionTransitionsRouteList({
    id,
    limit = 100,
    offset,
    sortBy = "created_at",
    direction = "asc",
    metadataFilter = "{}",
  }: {
    /**
     * ID of parent undefined
     */
    id: Common_uuid;
    /**
     * Limit the number of undefined items returned
     */
    limit?: Common_limit;
    /**
     * Offset the undefined items returned
     */
    offset: Common_offset;
    /**
     * Sort by a field
     */
    sortBy?: "created_at" | "updated_at" | "deleted_at";
    /**
     * Sort direction
     */
    direction?: "asc" | "desc";
    /**
     * JSON string of object that should be used to filter objects by metadata
     */
    metadataFilter?: string;
  }): CancelablePromise<{
    results: Array<{
      transitions: Array<Executions_Transition>;
    }>;
  }> {
    return this.httpRequest.request({
      method: "GET",
      url: "/executions/{id}/transitions",
      path: {
        id: id,
      },
      query: {
        limit: limit,
        offset: offset,
        sort_by: sortBy,
        direction: direction,
        metadata_filter: metadataFilter,
      },
    });
  }
  /**
   * Get undefined by id
   * @returns Jobs_JobStatus The request has succeeded.
   * @throws ApiError
   */
  public jobRouteGet({
    id,
  }: {
    /**
     * ID of the undefined
     */
    id: Common_uuid;
  }): CancelablePromise<Jobs_JobStatus> {
    return this.httpRequest.request({
      method: "GET",
      url: "/jobs/{id}",
      path: {
        id: id,
      },
    });
  }
  /**
   * List undefined items
   * @returns any The request has succeeded.
   * @throws ApiError
   */
  public sessionsRouteList({
    limit = 100,
    offset,
    sortBy = "created_at",
    direction = "asc",
    metadataFilter = "{}",
  }: {
    /**
     * Limit the number of undefined items returned
     */
    limit?: Common_limit;
    /**
     * Offset the undefined items returned
     */
    offset: Common_offset;
    /**
     * Sort by a field
     */
    sortBy?: "created_at" | "updated_at" | "deleted_at";
    /**
     * Sort direction
     */
    direction?: "asc" | "desc";
    /**
     * JSON string of object that should be used to filter objects by metadata
     */
    metadataFilter?: string;
  }): CancelablePromise<{
    results: Array<Sessions_Session>;
  }> {
    return this.httpRequest.request({
      method: "GET",
      url: "/sessions",
      query: {
        limit: limit,
        offset: offset,
        sort_by: sortBy,
        direction: direction,
        metadata_filter: metadataFilter,
      },
    });
  }
  /**
   * Create new undefined
   * @returns any The request has succeeded and a new resource has been created as a result.
   * @throws ApiError
   */
  public sessionsRouteCreate({
    requestBody,
  }: {
    requestBody: Sessions_CreateSessionRequest;
  }): CancelablePromise<{
    /**
     * ID of created undefined
     */
    id: Common_uuid;
    /**
     * When this resource was created as UTC date-time
     */
    readonly created_at: string;
    /**
     * IDs (if any) of jobs created as part of this request
     */
    jobs: Array<Common_uuid>;
  }> {
    return this.httpRequest.request({
      method: "POST",
      url: "/sessions",
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Create or update undefined (ID is required in payload; existing resource will be overwritten)
   * @returns any The request has succeeded.
   * @throws ApiError
   */
  public sessionsRouteCreateOrUpdate({
    requestBody,
  }: {
    requestBody: Sessions_CreateOrUpdateSessionRequest;
  }): CancelablePromise<{
    /**
     * ID of updated undefined
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
  }> {
    return this.httpRequest.request({
      method: "PUT",
      url: "/sessions",
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * List undefined items of parent undefined
   * @returns any The request has succeeded.
   * @throws ApiError
   */
  public historyRouteList({
    id,
    limit = 100,
    offset,
    sortBy = "created_at",
    direction = "asc",
    metadataFilter = "{}",
  }: {
    /**
     * ID of parent undefined
     */
    id: Common_uuid;
    /**
     * Limit the number of undefined items returned
     */
    limit?: Common_limit;
    /**
     * Offset the undefined items returned
     */
    offset: Common_offset;
    /**
     * Sort by a field
     */
    sortBy?: "created_at" | "updated_at" | "deleted_at";
    /**
     * Sort direction
     */
    direction?: "asc" | "desc";
    /**
     * JSON string of object that should be used to filter objects by metadata
     */
    metadataFilter?: string;
  }): CancelablePromise<{
    results: Array<Entries_History>;
  }> {
    return this.httpRequest.request({
      method: "GET",
      url: "/sessions/history/{id}",
      path: {
        id: id,
      },
      query: {
        limit: limit,
        offset: offset,
        sort_by: sortBy,
        direction: direction,
        metadata_filter: metadataFilter,
      },
    });
  }
  /**
   * Delete undefined by id
   * @returns any The request has been accepted for processing, but processing has not yet completed.
   * @throws ApiError
   */
  public historyRouteDelete({
    id,
  }: {
    /**
     * ID of the undefined
     */
    id: Common_uuid;
  }): CancelablePromise<{
    /**
     * ID of deleted undefined
     */
    id: Common_uuid;
    /**
     * When this resource was deleted as UTC date-time
     */
    readonly deleted_at: string;
    /**
     * IDs (if any) of jobs created as part of this request
     */
    jobs: Array<Common_uuid>;
  }> {
    return this.httpRequest.request({
      method: "DELETE",
      url: "/sessions/history/{id}",
      path: {
        id: id,
      },
    });
  }
  /**
   * Update undefined by id (overwrite)
   * @returns any The request has succeeded.
   * @throws ApiError
   */
  public sessionsRouteUpdate({
    id,
    requestBody,
  }: {
    /**
     * ID of the undefined
     */
    id: Common_uuid;
    requestBody: Sessions_UpdateSessionRequest;
  }): CancelablePromise<{
    /**
     * ID of updated undefined
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
  }> {
    return this.httpRequest.request({
      method: "PUT",
      url: "/sessions/{id}",
      path: {
        id: id,
      },
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Patch undefined by id (merge changes)
   * @returns any The request has succeeded.
   * @throws ApiError
   */
  public sessionsRoutePatch({
    id,
    requestBody,
  }: {
    /**
     * ID of the undefined
     */
    id: Common_uuid;
    requestBody: Sessions_PatchSessionRequest;
  }): CancelablePromise<{
    /**
     * ID of updated undefined
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
  }> {
    return this.httpRequest.request({
      method: "PATCH",
      url: "/sessions/{id}",
      path: {
        id: id,
      },
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Delete undefined by id
   * @returns any The request has been accepted for processing, but processing has not yet completed.
   * @throws ApiError
   */
  public sessionsRouteDelete({
    id,
  }: {
    /**
     * ID of the undefined
     */
    id: Common_uuid;
  }): CancelablePromise<{
    /**
     * ID of deleted undefined
     */
    id: Common_uuid;
    /**
     * When this resource was deleted as UTC date-time
     */
    readonly deleted_at: string;
    /**
     * IDs (if any) of jobs created as part of this request
     */
    jobs: Array<Common_uuid>;
  }> {
    return this.httpRequest.request({
      method: "DELETE",
      url: "/sessions/{id}",
      path: {
        id: id,
      },
    });
  }
  /**
   * Get undefined by id
   * @returns Sessions_Session The request has succeeded.
   * @throws ApiError
   */
  public sessionsRouteGet({
    id,
  }: {
    /**
     * ID of the undefined
     */
    id: Common_uuid;
  }): CancelablePromise<Sessions_Session> {
    return this.httpRequest.request({
      method: "GET",
      url: "/sessions/{id}",
      path: {
        id: id,
      },
    });
  }
  /**
   * List undefined items
   * @returns any The request has succeeded.
   * @throws ApiError
   */
  public tasksRouteList({
    limit = 100,
    offset,
    sortBy = "created_at",
    direction = "asc",
    metadataFilter = "{}",
  }: {
    /**
     * Limit the number of undefined items returned
     */
    limit?: Common_limit;
    /**
     * Offset the undefined items returned
     */
    offset: Common_offset;
    /**
     * Sort by a field
     */
    sortBy?: "created_at" | "updated_at" | "deleted_at";
    /**
     * Sort direction
     */
    direction?: "asc" | "desc";
    /**
     * JSON string of object that should be used to filter objects by metadata
     */
    metadataFilter?: string;
  }): CancelablePromise<{
    results: Array<Tasks_Task>;
  }> {
    return this.httpRequest.request({
      method: "GET",
      url: "/tasks",
      query: {
        limit: limit,
        offset: offset,
        sort_by: sortBy,
        direction: direction,
        metadata_filter: metadataFilter,
      },
    });
  }
  /**
   * Create or update undefined (ID is required in payload; existing resource will be overwritten)
   * @returns any The request has succeeded.
   * @throws ApiError
   */
  public tasksRouteCreateOrUpdate({
    requestBody,
  }: {
    requestBody: Tasks_CreateOrUpdateTaskRequest;
  }): CancelablePromise<{
    /**
     * ID of updated undefined
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
  }> {
    return this.httpRequest.request({
      method: "PUT",
      url: "/tasks",
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Create new undefined
   * @returns any The request has succeeded and a new resource has been created as a result.
   * @throws ApiError
   */
  public tasksRouteCreate({
    requestBody,
  }: {
    requestBody: Tasks_CreateTaskRequest;
  }): CancelablePromise<{
    /**
     * ID of created undefined
     */
    id: Common_uuid;
    /**
     * When this resource was created as UTC date-time
     */
    readonly created_at: string;
    /**
     * IDs (if any) of jobs created as part of this request
     */
    jobs: Array<Common_uuid>;
  }> {
    return this.httpRequest.request({
      method: "POST",
      url: "/tasks",
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Update undefined by id (overwrite)
   * @returns any The request has succeeded.
   * @throws ApiError
   */
  public tasksRouteUpdate({
    id,
    requestBody,
  }: {
    /**
     * ID of the undefined
     */
    id: Common_uuid;
    requestBody: Tasks_UpdateTaskRequest;
  }): CancelablePromise<{
    /**
     * ID of updated undefined
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
  }> {
    return this.httpRequest.request({
      method: "PUT",
      url: "/tasks/{id}",
      path: {
        id: id,
      },
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Patch undefined by id (merge changes)
   * @returns any The request has succeeded.
   * @throws ApiError
   */
  public tasksRoutePatch({
    id,
    requestBody,
  }: {
    /**
     * ID of the undefined
     */
    id: Common_uuid;
    requestBody: Tasks_PatchTaskRequest;
  }): CancelablePromise<{
    /**
     * ID of updated undefined
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
  }> {
    return this.httpRequest.request({
      method: "PATCH",
      url: "/tasks/{id}",
      path: {
        id: id,
      },
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Delete undefined by id
   * @returns any The request has been accepted for processing, but processing has not yet completed.
   * @throws ApiError
   */
  public tasksRouteDelete({
    id,
  }: {
    /**
     * ID of the undefined
     */
    id: Common_uuid;
  }): CancelablePromise<{
    /**
     * ID of deleted undefined
     */
    id: Common_uuid;
    /**
     * When this resource was deleted as UTC date-time
     */
    readonly deleted_at: string;
    /**
     * IDs (if any) of jobs created as part of this request
     */
    jobs: Array<Common_uuid>;
  }> {
    return this.httpRequest.request({
      method: "DELETE",
      url: "/tasks/{id}",
      path: {
        id: id,
      },
    });
  }
  /**
   * Create new undefined
   * @returns any The request has succeeded and a new resource has been created as a result.
   * @throws ApiError
   */
  public taskExecutionsRouteCreate({
    id,
    requestBody,
  }: {
    /**
     * ID of parent undefined
     */
    id: Common_uuid;
    requestBody: Executions_CreateExecutionRequest;
  }): CancelablePromise<{
    /**
     * ID of created undefined
     */
    id: Common_uuid;
    /**
     * When this resource was created as UTC date-time
     */
    readonly created_at: string;
    /**
     * IDs (if any) of jobs created as part of this request
     */
    jobs: Array<Common_uuid>;
  }> {
    return this.httpRequest.request({
      method: "POST",
      url: "/tasks/{id}/executions",
      path: {
        id: id,
      },
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * List undefined items of parent undefined
   * @returns any The request has succeeded.
   * @throws ApiError
   */
  public taskExecutionsRouteList({
    id,
    limit = 100,
    offset,
    sortBy = "created_at",
    direction = "asc",
    metadataFilter = "{}",
  }: {
    /**
     * ID of parent undefined
     */
    id: Common_uuid;
    /**
     * Limit the number of undefined items returned
     */
    limit?: Common_limit;
    /**
     * Offset the undefined items returned
     */
    offset: Common_offset;
    /**
     * Sort by a field
     */
    sortBy?: "created_at" | "updated_at" | "deleted_at";
    /**
     * Sort direction
     */
    direction?: "asc" | "desc";
    /**
     * JSON string of object that should be used to filter objects by metadata
     */
    metadataFilter?: string;
  }): CancelablePromise<{
    results: Array<Executions_Execution>;
  }> {
    return this.httpRequest.request({
      method: "GET",
      url: "/tasks/{id}/executions",
      path: {
        id: id,
      },
      query: {
        limit: limit,
        offset: offset,
        sort_by: sortBy,
        direction: direction,
        metadata_filter: metadataFilter,
      },
    });
  }
  /**
   * Resume an execution with a task token
   * @returns any The request has succeeded.
   * @throws ApiError
   */
  public taskExecutionsRouteResumeWithTaskToken({
    id,
    requestBody,
  }: {
    /**
     * ID of parent Task
     */
    id: Common_uuid;
    /**
     * Request to resume an execution with a task token
     */
    requestBody: Executions_TaskTokenResumeExecutionRequest;
  }): CancelablePromise<{
    /**
     * ID of updated undefined
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
  }> {
    return this.httpRequest.request({
      method: "PUT",
      url: "/tasks/{id}/executions",
      path: {
        id: id,
      },
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Update undefined by id (overwrite)
   * @returns any The request has succeeded.
   * @throws ApiError
   */
  public toolRouteUpdate({
    id,
    requestBody,
  }: {
    /**
     * ID of the undefined
     */
    id: Common_uuid;
    requestBody: Tools_UpdateToolRequest;
  }): CancelablePromise<{
    /**
     * ID of updated undefined
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
  }> {
    return this.httpRequest.request({
      method: "PUT",
      url: "/tools/{id}",
      path: {
        id: id,
      },
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Patch undefined by id (merge changes)
   * @returns any The request has succeeded.
   * @throws ApiError
   */
  public toolRoutePatch({
    id,
    requestBody,
  }: {
    /**
     * ID of the undefined
     */
    id: Common_uuid;
    requestBody: Tools_PatchToolRequest;
  }): CancelablePromise<{
    /**
     * ID of updated undefined
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
  }> {
    return this.httpRequest.request({
      method: "PATCH",
      url: "/tools/{id}",
      path: {
        id: id,
      },
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Delete undefined by id
   * @returns any The request has been accepted for processing, but processing has not yet completed.
   * @throws ApiError
   */
  public toolRouteDelete({
    id,
  }: {
    /**
     * ID of the undefined
     */
    id: Common_uuid;
  }): CancelablePromise<{
    /**
     * ID of deleted undefined
     */
    id: Common_uuid;
    /**
     * When this resource was deleted as UTC date-time
     */
    readonly deleted_at: string;
    /**
     * IDs (if any) of jobs created as part of this request
     */
    jobs: Array<Common_uuid>;
  }> {
    return this.httpRequest.request({
      method: "DELETE",
      url: "/tools/{id}",
      path: {
        id: id,
      },
    });
  }
  /**
   * List undefined items
   * @returns any The request has succeeded.
   * @throws ApiError
   */
  public usersRouteList({
    limit = 100,
    offset,
    sortBy = "created_at",
    direction = "asc",
    metadataFilter = "{}",
  }: {
    /**
     * Limit the number of undefined items returned
     */
    limit?: Common_limit;
    /**
     * Offset the undefined items returned
     */
    offset: Common_offset;
    /**
     * Sort by a field
     */
    sortBy?: "created_at" | "updated_at" | "deleted_at";
    /**
     * Sort direction
     */
    direction?: "asc" | "desc";
    /**
     * JSON string of object that should be used to filter objects by metadata
     */
    metadataFilter?: string;
  }): CancelablePromise<{
    results: Array<Users_User>;
  }> {
    return this.httpRequest.request({
      method: "GET",
      url: "/users",
      query: {
        limit: limit,
        offset: offset,
        sort_by: sortBy,
        direction: direction,
        metadata_filter: metadataFilter,
      },
    });
  }
  /**
   * Create new undefined
   * @returns any The request has succeeded and a new resource has been created as a result.
   * @throws ApiError
   */
  public usersRouteCreate({
    requestBody,
  }: {
    requestBody: Users_CreateUserRequest;
  }): CancelablePromise<{
    /**
     * ID of created undefined
     */
    id: Common_uuid;
    /**
     * When this resource was created as UTC date-time
     */
    readonly created_at: string;
    /**
     * IDs (if any) of jobs created as part of this request
     */
    jobs: Array<Common_uuid>;
  }> {
    return this.httpRequest.request({
      method: "POST",
      url: "/users",
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Create or update undefined (ID is required in payload; existing resource will be overwritten)
   * @returns any The request has succeeded.
   * @throws ApiError
   */
  public usersRouteCreateOrUpdate({
    requestBody,
  }: {
    requestBody: Users_CreateOrUpdateUserRequest;
  }): CancelablePromise<{
    /**
     * ID of updated undefined
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
  }> {
    return this.httpRequest.request({
      method: "PUT",
      url: "/users",
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Update undefined by id (overwrite)
   * @returns any The request has succeeded.
   * @throws ApiError
   */
  public usersRouteUpdate({
    id,
    requestBody,
  }: {
    /**
     * ID of the undefined
     */
    id: Common_uuid;
    requestBody: Users_UpdateUserRequest;
  }): CancelablePromise<{
    /**
     * ID of updated undefined
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
  }> {
    return this.httpRequest.request({
      method: "PUT",
      url: "/users/{id}",
      path: {
        id: id,
      },
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Patch undefined by id (merge changes)
   * @returns any The request has succeeded.
   * @throws ApiError
   */
  public usersRoutePatch({
    id,
    requestBody,
  }: {
    /**
     * ID of the undefined
     */
    id: Common_uuid;
    requestBody: Users_PatchUserRequest;
  }): CancelablePromise<{
    /**
     * ID of updated undefined
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
  }> {
    return this.httpRequest.request({
      method: "PATCH",
      url: "/users/{id}",
      path: {
        id: id,
      },
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Delete undefined by id
   * @returns any The request has been accepted for processing, but processing has not yet completed.
   * @throws ApiError
   */
  public usersRouteDelete({
    id,
  }: {
    /**
     * ID of the undefined
     */
    id: Common_uuid;
  }): CancelablePromise<{
    /**
     * ID of deleted undefined
     */
    id: Common_uuid;
    /**
     * When this resource was deleted as UTC date-time
     */
    readonly deleted_at: string;
    /**
     * IDs (if any) of jobs created as part of this request
     */
    jobs: Array<Common_uuid>;
  }> {
    return this.httpRequest.request({
      method: "DELETE",
      url: "/users/{id}",
      path: {
        id: id,
      },
    });
  }
  /**
   * Get undefined by id
   * @returns Users_User The request has succeeded.
   * @throws ApiError
   */
  public usersRouteGet({
    id,
  }: {
    /**
     * ID of the undefined
     */
    id: Common_uuid;
  }): CancelablePromise<Users_User> {
    return this.httpRequest.request({
      method: "GET",
      url: "/users/{id}",
      path: {
        id: id,
      },
    });
  }
  /**
   * List undefined items of parent undefined
   * @returns any The request has succeeded.
   * @throws ApiError
   */
  public userDocsRouteList({
    id,
    limit = 100,
    offset,
    sortBy = "created_at",
    direction = "asc",
    metadataFilter = "{}",
  }: {
    /**
     * ID of parent undefined
     */
    id: Common_uuid;
    /**
     * Limit the number of undefined items returned
     */
    limit?: Common_limit;
    /**
     * Offset the undefined items returned
     */
    offset: Common_offset;
    /**
     * Sort by a field
     */
    sortBy?: "created_at" | "updated_at" | "deleted_at";
    /**
     * Sort direction
     */
    direction?: "asc" | "desc";
    /**
     * JSON string of object that should be used to filter objects by metadata
     */
    metadataFilter?: string;
  }): CancelablePromise<{
    results: Array<Docs_Doc>;
  }> {
    return this.httpRequest.request({
      method: "GET",
      url: "/users/{id}/docs",
      path: {
        id: id,
      },
      query: {
        limit: limit,
        offset: offset,
        sort_by: sortBy,
        direction: direction,
        metadata_filter: metadataFilter,
      },
    });
  }
  /**
   * Search for documents owned by undefined
   * @returns any The request has succeeded.
   * @throws ApiError
   */
  public userDocsSearchRouteSearch({
    id,
    requestBody,
    limit = 100,
    offset,
    sortBy = "created_at",
    direction = "asc",
    metadataFilter = "{}",
  }: {
    /**
     * ID of the undefined
     */
    id: Common_uuid;
    requestBody: {
      body: Docs_DocSearchRequest;
    };
    /**
     * Limit the number of undefined items returned
     */
    limit?: Common_limit;
    /**
     * Offset the undefined items returned
     */
    offset: Common_offset;
    /**
     * Sort by a field
     */
    sortBy?: "created_at" | "updated_at" | "deleted_at";
    /**
     * Sort direction
     */
    direction?: "asc" | "desc";
    /**
     * JSON string of object that should be used to filter objects by metadata
     */
    metadataFilter?: string;
  }): CancelablePromise<{
    results: Array<Docs_DocReference>;
  }> {
    return this.httpRequest.request({
      method: "POST",
      url: "/users/{id}/search",
      path: {
        id: id,
      },
      query: {
        limit: limit,
        offset: offset,
        sort_by: sortBy,
        direction: direction,
        metadata_filter: metadataFilter,
      },
      body: requestBody,
      mediaType: "application/json",
    });
  }
}
