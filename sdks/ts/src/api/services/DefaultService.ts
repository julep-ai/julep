/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Agents_Agent } from "../models/Agents_Agent";
import type { Agents_CreateAgentRequest } from "../models/Agents_CreateAgentRequest";
import type { Agents_PatchAgentRequest } from "../models/Agents_PatchAgentRequest";
import type { Agents_UpdateAgentRequest } from "../models/Agents_UpdateAgentRequest";
import type { Chat_ChatInput } from "../models/Chat_ChatInput";
import type { Chat_ChunkChatResponse } from "../models/Chat_ChunkChatResponse";
import type { Chat_MessageChatResponse } from "../models/Chat_MessageChatResponse";
import type { Common_limit } from "../models/Common_limit";
import type { Common_offset } from "../models/Common_offset";
import type { Common_ResourceCreatedResponse } from "../models/Common_ResourceCreatedResponse";
import type { Common_ResourceDeletedResponse } from "../models/Common_ResourceDeletedResponse";
import type { Common_ResourceUpdatedResponse } from "../models/Common_ResourceUpdatedResponse";
import type { Common_uuid } from "../models/Common_uuid";
import type { Docs_CreateDocRequest } from "../models/Docs_CreateDocRequest";
import type { Docs_Doc } from "../models/Docs_Doc";
import type { Docs_DocSearchResponse } from "../models/Docs_DocSearchResponse";
import type { Docs_EmbedQueryRequest } from "../models/Docs_EmbedQueryRequest";
import type { Docs_EmbedQueryResponse } from "../models/Docs_EmbedQueryResponse";
import type { Docs_HybridDocSearchRequest } from "../models/Docs_HybridDocSearchRequest";
import type { Docs_TextOnlyDocSearchRequest } from "../models/Docs_TextOnlyDocSearchRequest";
import type { Docs_VectorDocSearchRequest } from "../models/Docs_VectorDocSearchRequest";
import type { Entries_History } from "../models/Entries_History";
import type { Executions_CreateExecutionRequest } from "../models/Executions_CreateExecutionRequest";
import type { Executions_Execution } from "../models/Executions_Execution";
import type { Executions_TaskTokenResumeExecutionRequest } from "../models/Executions_TaskTokenResumeExecutionRequest";
import type { Executions_Transition } from "../models/Executions_Transition";
import type { Executions_UpdateExecutionRequest } from "../models/Executions_UpdateExecutionRequest";
import type { Jobs_JobStatus } from "../models/Jobs_JobStatus";
import type { Sessions_CreateSessionRequest } from "../models/Sessions_CreateSessionRequest";
import type { Sessions_PatchSessionRequest } from "../models/Sessions_PatchSessionRequest";
import type { Sessions_Session } from "../models/Sessions_Session";
import type { Sessions_UpdateSessionRequest } from "../models/Sessions_UpdateSessionRequest";
import type { Tasks_CreateTaskRequest } from "../models/Tasks_CreateTaskRequest";
import type { Tasks_PatchTaskRequest } from "../models/Tasks_PatchTaskRequest";
import type { Tasks_Task } from "../models/Tasks_Task";
import type { Tasks_UpdateTaskRequest } from "../models/Tasks_UpdateTaskRequest";
import type { Tools_PatchToolRequest } from "../models/Tools_PatchToolRequest";
import type { Tools_Tool } from "../models/Tools_Tool";
import type { Tools_UpdateToolRequest } from "../models/Tools_UpdateToolRequest";
import type { Users_CreateUserRequest } from "../models/Users_CreateUserRequest";
import type { Users_PatchUserRequest } from "../models/Users_PatchUserRequest";
import type { Users_UpdateUserRequest } from "../models/Users_UpdateUserRequest";
import type { Users_User } from "../models/Users_User";
import type { CancelablePromise } from "../core/CancelablePromise";
import type { BaseHttpRequest } from "../core/BaseHttpRequest";
export class DefaultService {
  constructor(public readonly httpRequest: BaseHttpRequest) {}
  /**
   * List Agents (paginated)
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
     * Limit the number of items returned
     */
    limit?: Common_limit;
    /**
     * Offset the items returned
     */
    offset: Common_offset;
    /**
     * Sort by a field
     */
    sortBy?: "created_at" | "updated_at";
    /**
     * Sort direction
     */
    direction?: "asc" | "desc";
    /**
     * JSON string of object that should be used to filter objects by metadata
     */
    metadataFilter?: string;
  }): CancelablePromise<{
    items: Array<Agents_Agent>;
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
   * Create a new Agent
   * @returns Common_ResourceCreatedResponse The request has succeeded and a new resource has been created as a result.
   * @throws ApiError
   */
  public agentsRouteCreate({
    requestBody,
  }: {
    requestBody: Agents_CreateAgentRequest;
  }): CancelablePromise<Common_ResourceCreatedResponse> {
    return this.httpRequest.request({
      method: "POST",
      url: "/agents",
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Create or update an Agent
   * @returns Common_ResourceUpdatedResponse The request has succeeded.
   * @throws ApiError
   */
  public agentsRouteCreateOrUpdate({
    id,
    requestBody,
  }: {
    id: Common_uuid;
    requestBody: Agents_UpdateAgentRequest;
  }): CancelablePromise<Common_ResourceUpdatedResponse> {
    return this.httpRequest.request({
      method: "POST",
      url: "/agents/{id}",
      path: {
        id: id,
      },
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Update an existing Agent by id (overwrites existing values; use PATCH for merging instead)
   * @returns Common_ResourceUpdatedResponse The request has succeeded.
   * @throws ApiError
   */
  public agentsRouteUpdate({
    id,
    requestBody,
  }: {
    /**
     * ID of the resource
     */
    id: Common_uuid;
    requestBody: Agents_UpdateAgentRequest;
  }): CancelablePromise<Common_ResourceUpdatedResponse> {
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
   * Update an existing Agent by id (merges with existing values)
   * @returns Common_ResourceUpdatedResponse The request has succeeded.
   * @throws ApiError
   */
  public agentsRoutePatch({
    id,
    requestBody,
  }: {
    /**
     * ID of the resource
     */
    id: Common_uuid;
    requestBody: Agents_PatchAgentRequest;
  }): CancelablePromise<Common_ResourceUpdatedResponse> {
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
   * Delete Agent by id
   * @returns Common_ResourceDeletedResponse The request has been accepted for processing, but processing has not yet completed.
   * @throws ApiError
   */
  public agentsRouteDelete({
    id,
  }: {
    /**
     * ID of the resource
     */
    id: Common_uuid;
  }): CancelablePromise<Common_ResourceDeletedResponse> {
    return this.httpRequest.request({
      method: "DELETE",
      url: "/agents/{id}",
      path: {
        id: id,
      },
    });
  }
  /**
   * Get an Agent by id
   * @returns Agents_Agent The request has succeeded.
   * @throws ApiError
   */
  public agentsRouteGet({
    id,
  }: {
    /**
     * ID of the resource
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
   * List Docs owned by an Agent
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
     * ID of parent
     */
    id: Common_uuid;
    /**
     * Limit the number of items returned
     */
    limit?: Common_limit;
    /**
     * Offset the items returned
     */
    offset: Common_offset;
    /**
     * Sort by a field
     */
    sortBy?: "created_at" | "updated_at";
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
   * Create a Doc for this Agent
   * @returns Common_ResourceCreatedResponse The request has succeeded and a new resource has been created as a result.
   * @throws ApiError
   */
  public agentDocsRouteCreate({
    id,
    requestBody,
  }: {
    /**
     * ID of parent resource
     */
    id: Common_uuid;
    requestBody: Docs_CreateDocRequest;
  }): CancelablePromise<Common_ResourceCreatedResponse> {
    return this.httpRequest.request({
      method: "POST",
      url: "/agents/{id}/docs",
      path: {
        id: id,
      },
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Delete a Doc for this Agent
   * @returns Common_ResourceDeletedResponse The request has been accepted for processing, but processing has not yet completed.
   * @throws ApiError
   */
  public agentDocsRouteDelete({
    id,
    childId,
  }: {
    /**
     * ID of parent resource
     */
    id: Common_uuid;
    /**
     * ID of the resource to be deleted
     */
    childId: Common_uuid;
  }): CancelablePromise<Common_ResourceDeletedResponse> {
    return this.httpRequest.request({
      method: "DELETE",
      url: "/agents/{id}/docs/{child_id}",
      path: {
        id: id,
        child_id: childId,
      },
    });
  }
  /**
   * Search Docs owned by an Agent
   * @returns Docs_DocSearchResponse The request has succeeded.
   * @throws ApiError
   */
  public agentsDocsSearchRouteSearch({
    id,
    requestBody,
  }: {
    /**
     * ID of the parent
     */
    id: Common_uuid;
    requestBody: {
      body:
        | Docs_VectorDocSearchRequest
        | Docs_TextOnlyDocSearchRequest
        | Docs_HybridDocSearchRequest;
    };
  }): CancelablePromise<Docs_DocSearchResponse> {
    return this.httpRequest.request({
      method: "POST",
      url: "/agents/{id}/search",
      path: {
        id: id,
      },
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * List tasks (paginated)
   * @returns any The request has succeeded.
   * @throws ApiError
   */
  public tasksRouteList({
    id,
    limit = 100,
    offset,
    sortBy = "created_at",
    direction = "asc",
    metadataFilter = "{}",
  }: {
    /**
     * ID of parent
     */
    id: Common_uuid;
    /**
     * Limit the number of items returned
     */
    limit?: Common_limit;
    /**
     * Offset the items returned
     */
    offset: Common_offset;
    /**
     * Sort by a field
     */
    sortBy?: "created_at" | "updated_at";
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
      url: "/agents/{id}/tasks",
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
   * Create a new task
   * @returns Common_ResourceCreatedResponse The request has succeeded.
   * @throws ApiError
   */
  public tasksRouteCreate({
    id,
    requestBody,
  }: {
    /**
     * ID of parent resource
     */
    id: Common_uuid;
    requestBody: Tasks_CreateTaskRequest;
  }): CancelablePromise<Common_ResourceCreatedResponse> {
    return this.httpRequest.request({
      method: "POST",
      url: "/agents/{id}/tasks",
      path: {
        id: id,
      },
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Update an existing task (overwrite existing values)
   * @returns Common_ResourceUpdatedResponse The request has succeeded.
   * @throws ApiError
   */
  public tasksRouteUpdate({
    id,
    childId,
    requestBody,
  }: {
    /**
     * ID of parent resource
     */
    id: Common_uuid;
    /**
     * ID of the resource to be updated
     */
    childId: Common_uuid;
    requestBody: Tasks_UpdateTaskRequest;
  }): CancelablePromise<Common_ResourceUpdatedResponse> {
    return this.httpRequest.request({
      method: "PUT",
      url: "/agents/{id}/tasks/{child_id}",
      path: {
        id: id,
        child_id: childId,
      },
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Update an existing task (merges with existing values)
   * @returns Common_ResourceUpdatedResponse The request has succeeded.
   * @throws ApiError
   */
  public tasksRoutePatch({
    id,
    childId,
    requestBody,
  }: {
    /**
     * ID of parent resource
     */
    id: Common_uuid;
    /**
     * ID of the resource to be patched
     */
    childId: Common_uuid;
    requestBody: Tasks_PatchTaskRequest;
  }): CancelablePromise<Common_ResourceUpdatedResponse> {
    return this.httpRequest.request({
      method: "PATCH",
      url: "/agents/{id}/tasks/{child_id}",
      path: {
        id: id,
        child_id: childId,
      },
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Delete a task by its id
   * @returns Common_ResourceDeletedResponse The request has been accepted for processing, but processing has not yet completed.
   * @throws ApiError
   */
  public tasksRouteDelete({
    id,
    childId,
  }: {
    /**
     * ID of parent resource
     */
    id: Common_uuid;
    /**
     * ID of the resource to be deleted
     */
    childId: Common_uuid;
  }): CancelablePromise<Common_ResourceDeletedResponse> {
    return this.httpRequest.request({
      method: "DELETE",
      url: "/agents/{id}/tasks/{child_id}",
      path: {
        id: id,
        child_id: childId,
      },
    });
  }
  /**
   * List tools of the given agent
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
     * ID of parent
     */
    id: Common_uuid;
    /**
     * Limit the number of items returned
     */
    limit?: Common_limit;
    /**
     * Offset the items returned
     */
    offset: Common_offset;
    /**
     * Sort by a field
     */
    sortBy?: "created_at" | "updated_at";
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
   * Create a new tool for this agent
   * @returns Common_ResourceCreatedResponse The request has succeeded and a new resource has been created as a result.
   * @throws ApiError
   */
  public agentToolsRouteCreate({
    id,
    requestBody,
  }: {
    /**
     * ID of parent resource
     */
    id: Common_uuid;
    requestBody: Agents_CreateAgentRequest;
  }): CancelablePromise<Common_ResourceCreatedResponse> {
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
   * Update an existing tool (overwrite existing values)
   * @returns Common_ResourceUpdatedResponse The request has succeeded.
   * @throws ApiError
   */
  public agentToolsRouteUpdate({
    id,
    childId,
    requestBody,
  }: {
    /**
     * ID of parent resource
     */
    id: Common_uuid;
    /**
     * ID of the resource to be updated
     */
    childId: Common_uuid;
    requestBody: Tools_UpdateToolRequest;
  }): CancelablePromise<Common_ResourceUpdatedResponse> {
    return this.httpRequest.request({
      method: "PUT",
      url: "/agents/{id}/tools/{child_id}",
      path: {
        id: id,
        child_id: childId,
      },
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Update an existing tool (merges with existing values)
   * @returns Common_ResourceUpdatedResponse The request has succeeded.
   * @throws ApiError
   */
  public agentToolsRoutePatch({
    id,
    childId,
    requestBody,
  }: {
    /**
     * ID of parent resource
     */
    id: Common_uuid;
    /**
     * ID of the resource to be patched
     */
    childId: Common_uuid;
    requestBody: Tools_PatchToolRequest;
  }): CancelablePromise<Common_ResourceUpdatedResponse> {
    return this.httpRequest.request({
      method: "PATCH",
      url: "/agents/{id}/tools/{child_id}",
      path: {
        id: id,
        child_id: childId,
      },
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Delete an existing tool by id
   * @returns Common_ResourceDeletedResponse The request has been accepted for processing, but processing has not yet completed.
   * @throws ApiError
   */
  public agentToolsRouteDelete({
    id,
    childId,
  }: {
    /**
     * ID of parent resource
     */
    id: Common_uuid;
    /**
     * ID of the resource to be deleted
     */
    childId: Common_uuid;
  }): CancelablePromise<Common_ResourceDeletedResponse> {
    return this.httpRequest.request({
      method: "DELETE",
      url: "/agents/{id}/tools/{child_id}",
      path: {
        id: id,
        child_id: childId,
      },
    });
  }
  /**
   * Create or update a task
   * @returns Common_ResourceUpdatedResponse The request has succeeded and a new resource has been created as a result.
   * @throws ApiError
   */
  public tasksCreateOrUpdateRouteCreateOrUpdate({
    parentId,
    id,
    requestBody,
  }: {
    /**
     * ID of the agent
     */
    parentId: Common_uuid;
    id: Common_uuid;
    requestBody: Tasks_CreateTaskRequest;
  }): CancelablePromise<Common_ResourceUpdatedResponse> {
    return this.httpRequest.request({
      method: "POST",
      url: "/agents/{parent_id}/tasks/{id}",
      path: {
        parent_id: parentId,
        id: id,
      },
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Get Doc by id
   * @returns Docs_Doc The request has succeeded.
   * @throws ApiError
   */
  public individualDocsRouteGet({
    id,
  }: {
    /**
     * ID of the resource
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
   * Embed a query for search
   * @returns Docs_EmbedQueryResponse The request has succeeded.
   * @throws ApiError
   */
  public embedRouteEmbed({
    requestBody,
  }: {
    requestBody: {
      body: Docs_EmbedQueryRequest;
    };
  }): CancelablePromise<Docs_EmbedQueryResponse> {
    return this.httpRequest.request({
      method: "POST",
      url: "/embed",
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Resume an execution with a task token
   * @returns Common_ResourceUpdatedResponse The request has succeeded.
   * @throws ApiError
   */
  public executionsRouteResumeWithTaskToken({
    taskToken,
    requestBody,
  }: {
    /**
     * A Task Token is a unique identifier for a specific Task Execution.
     */
    taskToken: string;
    /**
     * Request to resume an execution with a task token
     */
    requestBody: Executions_TaskTokenResumeExecutionRequest;
  }): CancelablePromise<Common_ResourceUpdatedResponse> {
    return this.httpRequest.request({
      method: "POST",
      url: "/executions",
      query: {
        task_token: taskToken,
      },
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Get an Execution by id
   * @returns Executions_Execution The request has succeeded.
   * @throws ApiError
   */
  public executionsRouteGet({
    id,
  }: {
    /**
     * ID of the resource
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
   * Update an existing Execution
   * @returns Common_ResourceUpdatedResponse The request has succeeded.
   * @throws ApiError
   */
  public executionsRouteUpdate({
    id,
    requestBody,
  }: {
    /**
     * ID of the resource
     */
    id: Common_uuid;
    requestBody: Executions_UpdateExecutionRequest;
  }): CancelablePromise<Common_ResourceUpdatedResponse> {
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
   * List the Transitions of an Execution by id
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
     * ID of parent
     */
    id: Common_uuid;
    /**
     * Limit the number of items returned
     */
    limit?: Common_limit;
    /**
     * Offset the items returned
     */
    offset: Common_offset;
    /**
     * Sort by a field
     */
    sortBy?: "created_at" | "updated_at";
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
   * Get the status of an existing Job by its id
   * @returns Jobs_JobStatus The request has succeeded.
   * @throws ApiError
   */
  public jobRouteGet({
    id,
  }: {
    /**
     * ID of the resource
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
   * List sessions (paginated)
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
     * Limit the number of items returned
     */
    limit?: Common_limit;
    /**
     * Offset the items returned
     */
    offset: Common_offset;
    /**
     * Sort by a field
     */
    sortBy?: "created_at" | "updated_at";
    /**
     * Sort direction
     */
    direction?: "asc" | "desc";
    /**
     * JSON string of object that should be used to filter objects by metadata
     */
    metadataFilter?: string;
  }): CancelablePromise<{
    items: Array<Sessions_Session>;
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
   * Create a new session
   * @returns Common_ResourceCreatedResponse The request has succeeded and a new resource has been created as a result.
   * @throws ApiError
   */
  public sessionsRouteCreate({
    requestBody,
  }: {
    requestBody: Sessions_CreateSessionRequest;
  }): CancelablePromise<Common_ResourceCreatedResponse> {
    return this.httpRequest.request({
      method: "POST",
      url: "/sessions",
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Create or update a session
   * @returns Common_ResourceUpdatedResponse The request has succeeded.
   * @throws ApiError
   */
  public sessionsRouteCreateOrUpdate({
    id,
    requestBody,
  }: {
    id: Common_uuid;
    requestBody: Sessions_CreateSessionRequest;
  }): CancelablePromise<Common_ResourceUpdatedResponse> {
    return this.httpRequest.request({
      method: "POST",
      url: "/sessions/{id}",
      path: {
        id: id,
      },
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Update an existing session by its id (overwrites all existing values)
   * @returns Common_ResourceUpdatedResponse The request has succeeded.
   * @throws ApiError
   */
  public sessionsRouteUpdate({
    id,
    requestBody,
  }: {
    /**
     * ID of the resource
     */
    id: Common_uuid;
    requestBody: Sessions_UpdateSessionRequest;
  }): CancelablePromise<Common_ResourceUpdatedResponse> {
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
   * Update an existing session by its id (merges with existing values)
   * @returns Common_ResourceUpdatedResponse The request has succeeded.
   * @throws ApiError
   */
  public sessionsRoutePatch({
    id,
    requestBody,
  }: {
    /**
     * ID of the resource
     */
    id: Common_uuid;
    requestBody: Sessions_PatchSessionRequest;
  }): CancelablePromise<Common_ResourceUpdatedResponse> {
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
   * Delete a session by its id
   * @returns Common_ResourceDeletedResponse The request has been accepted for processing, but processing has not yet completed.
   * @throws ApiError
   */
  public sessionsRouteDelete({
    id,
  }: {
    /**
     * ID of the resource
     */
    id: Common_uuid;
  }): CancelablePromise<Common_ResourceDeletedResponse> {
    return this.httpRequest.request({
      method: "DELETE",
      url: "/sessions/{id}",
      path: {
        id: id,
      },
    });
  }
  /**
   * Get a session by id
   * @returns Sessions_Session The request has succeeded.
   * @throws ApiError
   */
  public sessionsRouteGet({
    id,
  }: {
    /**
     * ID of the resource
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
   * Generate a response from the model
   * @returns any The request has succeeded.
   * @throws ApiError
   */
  public chatRouteGenerate({
    id,
    requestBody,
  }: {
    /**
     * The session ID
     */
    id: Common_uuid;
    /**
     * Request to generate a response from the model
     */
    requestBody: Chat_ChatInput;
  }): CancelablePromise<Chat_ChunkChatResponse | Chat_MessageChatResponse> {
    return this.httpRequest.request({
      method: "POST",
      url: "/sessions/{id}/chat",
      path: {
        id: id,
      },
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Clear the history of a Session (resets the Session)
   * @returns Common_ResourceDeletedResponse The request has been accepted for processing, but processing has not yet completed.
   * @throws ApiError
   */
  public historyRouteDelete({
    id,
  }: {
    /**
     * ID of the resource
     */
    id: Common_uuid;
  }): CancelablePromise<Common_ResourceDeletedResponse> {
    return this.httpRequest.request({
      method: "DELETE",
      url: "/sessions/{id}/history",
      path: {
        id: id,
      },
    });
  }
  /**
   * Get history of a Session
   * @returns Entries_History The request has succeeded.
   * @throws ApiError
   */
  public historyRouteHistory({
    id,
  }: {
    /**
     * ID of parent
     */
    id: Common_uuid;
  }): CancelablePromise<Entries_History> {
    return this.httpRequest.request({
      method: "GET",
      url: "/sessions/{id}/history",
      path: {
        id: id,
      },
    });
  }
  /**
   * Create an execution for the given task
   * @returns Common_ResourceCreatedResponse The request has succeeded and a new resource has been created as a result.
   * @throws ApiError
   */
  public taskExecutionsRouteCreate({
    id,
    requestBody,
  }: {
    /**
     * ID of parent resource
     */
    id: Common_uuid;
    requestBody: Executions_CreateExecutionRequest;
  }): CancelablePromise<Common_ResourceCreatedResponse> {
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
   * List executions of the given task
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
     * ID of parent
     */
    id: Common_uuid;
    /**
     * Limit the number of items returned
     */
    limit?: Common_limit;
    /**
     * Offset the items returned
     */
    offset: Common_offset;
    /**
     * Sort by a field
     */
    sortBy?: "created_at" | "updated_at";
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
   * List users (paginated)
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
     * Limit the number of items returned
     */
    limit?: Common_limit;
    /**
     * Offset the items returned
     */
    offset: Common_offset;
    /**
     * Sort by a field
     */
    sortBy?: "created_at" | "updated_at";
    /**
     * Sort direction
     */
    direction?: "asc" | "desc";
    /**
     * JSON string of object that should be used to filter objects by metadata
     */
    metadataFilter?: string;
  }): CancelablePromise<{
    items: Array<Users_User>;
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
   * Create a new user
   * @returns Common_ResourceCreatedResponse The request has succeeded and a new resource has been created as a result.
   * @throws ApiError
   */
  public usersRouteCreate({
    requestBody,
  }: {
    requestBody: Users_CreateUserRequest;
  }): CancelablePromise<Common_ResourceCreatedResponse> {
    return this.httpRequest.request({
      method: "POST",
      url: "/users",
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Create or update a user
   * @returns Common_ResourceUpdatedResponse The request has succeeded.
   * @throws ApiError
   */
  public usersRouteCreateOrUpdate({
    id,
    requestBody,
  }: {
    id: Common_uuid;
    requestBody: Users_CreateUserRequest;
  }): CancelablePromise<Common_ResourceUpdatedResponse> {
    return this.httpRequest.request({
      method: "POST",
      url: "/users/{id}",
      path: {
        id: id,
      },
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Update an existing user by id (overwrite existing values)
   * @returns Common_ResourceUpdatedResponse The request has succeeded.
   * @throws ApiError
   */
  public usersRouteUpdate({
    id,
    requestBody,
  }: {
    /**
     * ID of the resource
     */
    id: Common_uuid;
    requestBody: Users_UpdateUserRequest;
  }): CancelablePromise<Common_ResourceUpdatedResponse> {
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
   * Update an existing user by id (merge with existing values)
   * @returns Common_ResourceUpdatedResponse The request has succeeded.
   * @throws ApiError
   */
  public usersRoutePatch({
    id,
    requestBody,
  }: {
    /**
     * ID of the resource
     */
    id: Common_uuid;
    requestBody: Users_PatchUserRequest;
  }): CancelablePromise<Common_ResourceUpdatedResponse> {
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
   * Delete a user by id
   * @returns Common_ResourceDeletedResponse The request has been accepted for processing, but processing has not yet completed.
   * @throws ApiError
   */
  public usersRouteDelete({
    id,
  }: {
    /**
     * ID of the resource
     */
    id: Common_uuid;
  }): CancelablePromise<Common_ResourceDeletedResponse> {
    return this.httpRequest.request({
      method: "DELETE",
      url: "/users/{id}",
      path: {
        id: id,
      },
    });
  }
  /**
   * Get a user by id
   * @returns Users_User The request has succeeded.
   * @throws ApiError
   */
  public usersRouteGet({
    id,
  }: {
    /**
     * ID of the resource
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
   * List Docs owned by a User
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
     * ID of parent
     */
    id: Common_uuid;
    /**
     * Limit the number of items returned
     */
    limit?: Common_limit;
    /**
     * Offset the items returned
     */
    offset: Common_offset;
    /**
     * Sort by a field
     */
    sortBy?: "created_at" | "updated_at";
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
   * Create a Doc for this User
   * @returns Common_ResourceCreatedResponse The request has succeeded and a new resource has been created as a result.
   * @throws ApiError
   */
  public userDocsRouteCreate({
    id,
    requestBody,
  }: {
    /**
     * ID of parent resource
     */
    id: Common_uuid;
    requestBody: Docs_CreateDocRequest;
  }): CancelablePromise<Common_ResourceCreatedResponse> {
    return this.httpRequest.request({
      method: "POST",
      url: "/users/{id}/docs",
      path: {
        id: id,
      },
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Delete a Doc for this User
   * @returns Common_ResourceDeletedResponse The request has been accepted for processing, but processing has not yet completed.
   * @throws ApiError
   */
  public userDocsRouteDelete({
    id,
    childId,
  }: {
    /**
     * ID of parent resource
     */
    id: Common_uuid;
    /**
     * ID of the resource to be deleted
     */
    childId: Common_uuid;
  }): CancelablePromise<Common_ResourceDeletedResponse> {
    return this.httpRequest.request({
      method: "DELETE",
      url: "/users/{id}/docs/{child_id}",
      path: {
        id: id,
        child_id: childId,
      },
    });
  }
  /**
   * Search Docs owned by a User
   * @returns Docs_DocSearchResponse The request has succeeded.
   * @throws ApiError
   */
  public userDocsSearchRouteSearch({
    id,
    requestBody,
  }: {
    /**
     * ID of the parent
     */
    id: Common_uuid;
    requestBody: {
      body:
        | Docs_VectorDocSearchRequest
        | Docs_TextOnlyDocSearchRequest
        | Docs_HybridDocSearchRequest;
    };
  }): CancelablePromise<Docs_DocSearchResponse> {
    return this.httpRequest.request({
      method: "POST",
      url: "/users/{id}/search",
      path: {
        id: id,
      },
      body: requestBody,
      mediaType: "application/json",
    });
  }
}
