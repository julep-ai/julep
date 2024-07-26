/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Chat_ChunkChatResponse } from "../models/Chat_ChunkChatResponse";
import type { Chat_CompletionResponseFormat } from "../models/Chat_CompletionResponseFormat";
import type { Chat_GenerationPreset } from "../models/Chat_GenerationPreset";
import type { Chat_MessageChatResponse } from "../models/Chat_MessageChatResponse";
import type { Common_identifierSafeUnicode } from "../models/Common_identifierSafeUnicode";
import type { Common_limit } from "../models/Common_limit";
import type { Common_logit_bias } from "../models/Common_logit_bias";
import type { Common_offset } from "../models/Common_offset";
import type { Common_ResourceCreatedResponse } from "../models/Common_ResourceCreatedResponse";
import type { Common_ResourceDeletedResponse } from "../models/Common_ResourceDeletedResponse";
import type { Common_ResourceUpdatedResponse } from "../models/Common_ResourceUpdatedResponse";
import type { Common_uuid } from "../models/Common_uuid";
import type { Docs_Doc } from "../models/Docs_Doc";
import type { Docs_DocReference } from "../models/Docs_DocReference";
import type { Docs_HybridDocSearchRequest } from "../models/Docs_HybridDocSearchRequest";
import type { Docs_TextOnlyDocSearchRequest } from "../models/Docs_TextOnlyDocSearchRequest";
import type { Docs_VectorDocSearchRequest } from "../models/Docs_VectorDocSearchRequest";
import type { Entries_History } from "../models/Entries_History";
import type { Entries_InputChatMLMessage } from "../models/Entries_InputChatMLMessage";
import type { Executions_CreateExecutionRequest } from "../models/Executions_CreateExecutionRequest";
import type { Executions_Execution } from "../models/Executions_Execution";
import type { Executions_TaskTokenResumeExecutionRequest } from "../models/Executions_TaskTokenResumeExecutionRequest";
import type { Executions_Transition } from "../models/Executions_Transition";
import type { Executions_UpdateExecutionRequest } from "../models/Executions_UpdateExecutionRequest";
import type { Tasks_CreateTaskRequest } from "../models/Tasks_CreateTaskRequest";
import type { Tasks_PatchTaskRequest } from "../models/Tasks_PatchTaskRequest";
import type { Tasks_Task } from "../models/Tasks_Task";
import type { Tasks_UpdateTaskRequest } from "../models/Tasks_UpdateTaskRequest";
import type { Tools_FunctionTool } from "../models/Tools_FunctionTool";
import type { Tools_NamedToolChoice } from "../models/Tools_NamedToolChoice";
import type { CancelablePromise } from "../core/CancelablePromise";
import type { BaseHttpRequest } from "../core/BaseHttpRequest";
export class DefaultService {
  constructor(public readonly httpRequest: BaseHttpRequest) {}
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
   * Search Docs owned by an Agent
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
     * ID of the parent
     */
    id: Common_uuid;
    requestBody: {
      body:
        | Docs_VectorDocSearchRequest
        | Docs_TextOnlyDocSearchRequest
        | Docs_HybridDocSearchRequest;
    };
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
   * @returns Common_ResourceCreatedResponse The request has succeeded and a new resource has been created as a result.
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
   * Delete an existing Doc by id
   * @returns Common_ResourceDeletedResponse The request has been accepted for processing, but processing has not yet completed.
   * @throws ApiError
   */
  public individualDocsRouteDelete({
    id,
  }: {
    /**
     * ID of the resource
     */
    id: Common_uuid;
  }): CancelablePromise<Common_ResourceDeletedResponse> {
    return this.httpRequest.request({
      method: "DELETE",
      url: "/docs/{id}",
      path: {
        id: id,
      },
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
    requestBody:
      | {
          /**
           * A list of new input messages comprising the conversation so far.
           */
          messages: Array<Entries_InputChatMLMessage>;
          /**
           * (Advanced) List of tools that are provided in addition to agent's default set of tools.
           */
          tools?: Array<Tools_FunctionTool>;
          /**
           * Can be one of existing tools given to the agent earlier or the ones provided in this request.
           */
          tool_choice?: "auto" | "none" | Tools_NamedToolChoice;
          /**
           * Whether previous memories should be recalled or not (will be enabled in a future release)
           */
          readonly recall: boolean;
          /**
           * Whether this interaction should form new memories or not (will be enabled in a future release)
           */
          readonly remember: boolean;
          /**
           * Whether this interaction should be stored in the session history or not
           */
          save: boolean;
          /**
           * Identifier of the model to be used
           */
          model?: Common_identifierSafeUnicode;
          /**
           * Indicates if the server should stream the response as it's generated
           */
          stream: boolean;
          /**
           * Up to 4 sequences where the API will stop generating further tokens.
           */
          stop?: Array<string>;
          /**
           * If specified, the system will make a best effort to sample deterministically for that particular seed value
           */
          seed?: number;
          /**
           * The maximum number of tokens to generate in the chat completion
           */
          max_tokens?: number;
          /**
           * Modify the likelihood of specified tokens appearing in the completion
           */
          logit_bias?: Record<string, Common_logit_bias>;
          /**
           * Response format (set to `json_object` to restrict output to JSON)
           */
          response_format?: Chat_CompletionResponseFormat;
          /**
           * Agent ID of the agent to use for this interaction. (Only applicable for multi-agent sessions)
           */
          agent?: Common_uuid;
          /**
           * Generation preset (one of: problem_solving, conversational, fun, prose, creative, business, deterministic, code, multilingual)
           */
          preset?: Chat_GenerationPreset;
        }
      | {
          /**
           * A list of new input messages comprising the conversation so far.
           */
          messages: Array<Entries_InputChatMLMessage>;
          /**
           * (Advanced) List of tools that are provided in addition to agent's default set of tools.
           */
          tools?: Array<Tools_FunctionTool>;
          /**
           * Can be one of existing tools given to the agent earlier or the ones provided in this request.
           */
          tool_choice?: "auto" | "none" | Tools_NamedToolChoice;
          /**
           * Whether previous memories should be recalled or not (will be enabled in a future release)
           */
          readonly recall: boolean;
          /**
           * Whether this interaction should form new memories or not (will be enabled in a future release)
           */
          readonly remember: boolean;
          /**
           * Whether this interaction should be stored in the session history or not
           */
          save: boolean;
          /**
           * Identifier of the model to be used
           */
          model?: Common_identifierSafeUnicode;
          /**
           * Indicates if the server should stream the response as it's generated
           */
          stream: boolean;
          /**
           * Up to 4 sequences where the API will stop generating further tokens.
           */
          stop?: Array<string>;
          /**
           * If specified, the system will make a best effort to sample deterministically for that particular seed value
           */
          seed?: number;
          /**
           * The maximum number of tokens to generate in the chat completion
           */
          max_tokens?: number;
          /**
           * Modify the likelihood of specified tokens appearing in the completion
           */
          logit_bias?: Record<string, Common_logit_bias>;
          /**
           * Response format (set to `json_object` to restrict output to JSON)
           */
          response_format?: Chat_CompletionResponseFormat;
          /**
           * Agent ID of the agent to use for this interaction. (Only applicable for multi-agent sessions)
           */
          agent?: Common_uuid;
          /**
           * Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.
           */
          frequency_penalty?: number;
          /**
           * Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.
           */
          presence_penalty?: number;
          /**
           * What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic.
           */
          temperature?: number;
          /**
           * Defaults to 1 An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered.  We generally recommend altering this or temperature but not both.
           */
          top_p?: number;
        }
      | {
          /**
           * A list of new input messages comprising the conversation so far.
           */
          messages: Array<Entries_InputChatMLMessage>;
          /**
           * (Advanced) List of tools that are provided in addition to agent's default set of tools.
           */
          tools?: Array<Tools_FunctionTool>;
          /**
           * Can be one of existing tools given to the agent earlier or the ones provided in this request.
           */
          tool_choice?: "auto" | "none" | Tools_NamedToolChoice;
          /**
           * Whether previous memories should be recalled or not (will be enabled in a future release)
           */
          readonly recall: boolean;
          /**
           * Whether this interaction should form new memories or not (will be enabled in a future release)
           */
          readonly remember: boolean;
          /**
           * Whether this interaction should be stored in the session history or not
           */
          save: boolean;
          /**
           * Identifier of the model to be used
           */
          model?: Common_identifierSafeUnicode;
          /**
           * Indicates if the server should stream the response as it's generated
           */
          stream: boolean;
          /**
           * Up to 4 sequences where the API will stop generating further tokens.
           */
          stop?: Array<string>;
          /**
           * If specified, the system will make a best effort to sample deterministically for that particular seed value
           */
          seed?: number;
          /**
           * The maximum number of tokens to generate in the chat completion
           */
          max_tokens?: number;
          /**
           * Modify the likelihood of specified tokens appearing in the completion
           */
          logit_bias?: Record<string, Common_logit_bias>;
          /**
           * Response format (set to `json_object` to restrict output to JSON)
           */
          response_format?: Chat_CompletionResponseFormat;
          /**
           * Agent ID of the agent to use for this interaction. (Only applicable for multi-agent sessions)
           */
          agent?: Common_uuid;
          /**
           * Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.
           */
          repetition_penalty?: number;
          /**
           * Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize number of tokens generated.
           */
          length_penalty?: number;
          /**
           * What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic.
           */
          temperature?: number;
          /**
           * Defaults to 1 An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered.  We generally recommend altering this or temperature but not both.
           */
          top_p?: number;
          /**
           * Minimum probability compared to leading token to be considered
           */
          min_p?: number;
        };
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
   * Get history of a Session (paginated)
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
      url: "/sessions/{id}/history",
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
   * @returns Common_ResourceUpdatedResponse The request has succeeded.
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
  }): CancelablePromise<Common_ResourceUpdatedResponse> {
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
   * Update an existing Execution
   * @returns Common_ResourceUpdatedResponse The request has succeeded.
   * @throws ApiError
   */
  public taskExecutionsRouteUpdate({
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
    requestBody: Executions_UpdateExecutionRequest;
  }): CancelablePromise<Common_ResourceUpdatedResponse> {
    return this.httpRequest.request({
      method: "PUT",
      url: "/tasks/{id}/executions/{child_id}",
      path: {
        id: id,
        child_id: childId,
      },
      body: requestBody,
      mediaType: "application/json",
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
   * Search Docs owned by a User
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
     * ID of the parent
     */
    id: Common_uuid;
    requestBody: {
      body:
        | Docs_VectorDocSearchRequest
        | Docs_TextOnlyDocSearchRequest
        | Docs_HybridDocSearchRequest;
    };
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
