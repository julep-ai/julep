/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Agent } from "../models/Agent";
import type { ChatInput } from "../models/ChatInput";
import type { ChatMLMessage } from "../models/ChatMLMessage";
import type { ChatResponse } from "../models/ChatResponse";
import type { CreateAgentRequest } from "../models/CreateAgentRequest";
import type { CreateDoc } from "../models/CreateDoc";
import type { CreateExecution } from "../models/CreateExecution";
import type { CreateSessionRequest } from "../models/CreateSessionRequest";
import type { CreateTask } from "../models/CreateTask";
import type { CreateToolRequest } from "../models/CreateToolRequest";
import type { CreateUserRequest } from "../models/CreateUserRequest";
import type { Doc } from "../models/Doc";
import type { Execution } from "../models/Execution";
import type { ExecutionTransition } from "../models/ExecutionTransition";
import type { JobStatus } from "../models/JobStatus";
import type { Memory } from "../models/Memory";
import type { PatchAgentRequest } from "../models/PatchAgentRequest";
import type { PatchSessionRequest } from "../models/PatchSessionRequest";
import type { PatchToolRequest } from "../models/PatchToolRequest";
import type { PatchUserRequest } from "../models/PatchUserRequest";
import type { ResourceCreatedResponse } from "../models/ResourceCreatedResponse";
import type { ResourceDeletedResponse } from "../models/ResourceDeletedResponse";
import type { ResourceUpdatedResponse } from "../models/ResourceUpdatedResponse";
import type { Session } from "../models/Session";
import type { Suggestion } from "../models/Suggestion";
import type { Task } from "../models/Task";
import type { Tool } from "../models/Tool";
import type { ToolResponse } from "../models/ToolResponse";
import type { UpdateAgentRequest } from "../models/UpdateAgentRequest";
import type { UpdateSessionRequest } from "../models/UpdateSessionRequest";
import type { UpdateToolRequest } from "../models/UpdateToolRequest";
import type { UpdateUserRequest } from "../models/UpdateUserRequest";
import type { User } from "../models/User";
import type { CancelablePromise } from "../core/CancelablePromise";
import type { BaseHttpRequest } from "../core/BaseHttpRequest";
export class DefaultService {
  constructor(public readonly httpRequest: BaseHttpRequest) {}
  /**
   * Create a new session
   * Create a session between an agent and a user
   * @returns ResourceCreatedResponse Session successfully created
   * @throws ApiError
   */
  public createSession({
    requestBody,
  }: {
    /**
     * Session initialization options
     */
    requestBody?: CreateSessionRequest;
  }): CancelablePromise<ResourceCreatedResponse> {
    return this.httpRequest.request({
      method: "POST",
      url: "/sessions",
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * List sessions
   * List sessions created (use limit/offset pagination to get large number of sessions; sorted by descending order of `created_at` by default)
   * @returns any List of sessions (sorted created_at descending order) with limit+offset pagination
   * @throws ApiError
   */
  public listSessions({
    limit = 100,
    offset,
    metadataFilter = "{}",
    sortBy = "created_at",
    order = "desc",
  }: {
    /**
     * Number of sessions to return
     */
    limit?: number;
    /**
     * Number of sessions to skip (sorted created_at descending order)
     */
    offset?: number;
    /**
     * JSON object that should be used to filter objects by metadata
     */
    metadataFilter?: string;
    /**
     * Which field to sort by: `created_at` or `updated_at`
     */
    sortBy?: "created_at" | "updated_at";
    /**
     * Which order should the sort be: `asc` (ascending) or `desc` (descending)
     */
    order?: "asc" | "desc";
  }): CancelablePromise<{
    items: Array<Session>;
  }> {
    return this.httpRequest.request({
      method: "GET",
      url: "/sessions",
      query: {
        limit: limit,
        offset: offset,
        metadata_filter: metadataFilter,
        sort_by: sortBy,
        order: order,
      },
    });
  }
  /**
   * Create a new user
   * Create a new user
   * @returns ResourceCreatedResponse User successfully created
   * @throws ApiError
   */
  public createUser({
    requestBody,
  }: {
    /**
     * User create options
     */
    requestBody?: CreateUserRequest;
  }): CancelablePromise<ResourceCreatedResponse> {
    return this.httpRequest.request({
      method: "POST",
      url: "/users",
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * List users
   * List users created (use limit/offset pagination to get large number of sessions; sorted by descending order of `created_at` by default)
   * @returns any List of users (sorted created_at descending order) with limit+offset pagination
   * @throws ApiError
   */
  public listUsers({
    limit = 100,
    offset,
    metadataFilter = "{}",
    sortBy = "created_at",
    order = "desc",
  }: {
    /**
     * Number of items to return
     */
    limit?: number;
    /**
     * Number of items to skip (sorted created_at descending order)
     */
    offset?: number;
    /**
     * JSON object that should be used to filter objects by metadata
     */
    metadataFilter?: string;
    /**
     * Which field to sort by: `created_at` or `updated_at`
     */
    sortBy?: "created_at" | "updated_at";
    /**
     * Which order should the sort be: `asc` (ascending) or `desc` (descending)
     */
    order?: "asc" | "desc";
  }): CancelablePromise<{
    items: Array<User>;
  }> {
    return this.httpRequest.request({
      method: "GET",
      url: "/users",
      query: {
        limit: limit,
        offset: offset,
        metadata_filter: metadataFilter,
        sort_by: sortBy,
        order: order,
      },
    });
  }
  /**
   * Create a new agent
   * Create a new agent
   * @returns ResourceCreatedResponse Agent successfully created
   * @throws ApiError
   */
  public createAgent({
    requestBody,
  }: {
    /**
     * Agent create options
     */
    requestBody?: CreateAgentRequest;
  }): CancelablePromise<ResourceCreatedResponse> {
    return this.httpRequest.request({
      method: "POST",
      url: "/agents",
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * List agents
   * List agents created (use limit/offset pagination to get large number of sessions; sorted by descending order of `created_at` by default)
   * @returns any List of agents (sorted created_at descending order) with limit+offset pagination
   * @throws ApiError
   */
  public listAgents({
    limit = 100,
    offset,
    metadataFilter = "{}",
    sortBy = "created_at",
    order = "desc",
  }: {
    /**
     * Number of items to return
     */
    limit?: number;
    /**
     * Number of items to skip (sorted created_at descending order)
     */
    offset?: number;
    /**
     * JSON object that should be used to filter objects by metadata
     */
    metadataFilter?: string;
    /**
     * Which field to sort by: `created_at` or `updated_at`
     */
    sortBy?: "created_at" | "updated_at";
    /**
     * Which order should the sort be: `asc` (ascending) or `desc` (descending)
     */
    order?: "asc" | "desc";
  }): CancelablePromise<{
    items: Array<Agent>;
  }> {
    return this.httpRequest.request({
      method: "GET",
      url: "/agents",
      query: {
        limit: limit,
        offset: offset,
        metadata_filter: metadataFilter,
        sort_by: sortBy,
        order: order,
      },
    });
  }
  /**
   * Get details of the session
   * @returns Session
   * @throws ApiError
   */
  public getSession({
    sessionId,
  }: {
    sessionId: string;
  }): CancelablePromise<Session> {
    return this.httpRequest.request({
      method: "GET",
      url: "/sessions/{session_id}",
      path: {
        session_id: sessionId,
      },
    });
  }
  /**
   * Delete session
   * @returns ResourceDeletedResponse
   * @throws ApiError
   */
  public deleteSession({
    sessionId,
  }: {
    sessionId: string;
  }): CancelablePromise<ResourceDeletedResponse> {
    return this.httpRequest.request({
      method: "DELETE",
      url: "/sessions/{session_id}",
      path: {
        session_id: sessionId,
      },
    });
  }
  /**
   * Update session parameters
   * @returns ResourceUpdatedResponse
   * @throws ApiError
   */
  public updateSession({
    sessionId,
    requestBody,
  }: {
    sessionId: string;
    requestBody?: UpdateSessionRequest;
  }): CancelablePromise<ResourceUpdatedResponse> {
    return this.httpRequest.request({
      method: "PUT",
      url: "/sessions/{session_id}",
      path: {
        session_id: sessionId,
      },
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Patch Session parameters (merge instead of replace)
   * @returns ResourceUpdatedResponse
   * @throws ApiError
   */
  public patchSession({
    sessionId,
    requestBody,
  }: {
    sessionId: string;
    requestBody?: PatchSessionRequest;
  }): CancelablePromise<ResourceUpdatedResponse> {
    return this.httpRequest.request({
      method: "PATCH",
      url: "/sessions/{session_id}",
      path: {
        session_id: sessionId,
      },
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Get autogenerated suggestions for session user and agent
   * Sorted (created_at descending)
   * @returns any
   * @throws ApiError
   */
  public getSuggestions({
    sessionId,
    limit = 100,
    offset,
  }: {
    sessionId: string;
    limit?: number;
    offset?: number;
  }): CancelablePromise<{
    items?: Array<Suggestion>;
  }> {
    return this.httpRequest.request({
      method: "GET",
      url: "/sessions/{session_id}/suggestions",
      path: {
        session_id: sessionId,
      },
      query: {
        limit: limit,
        offset: offset,
      },
    });
  }
  /**
   * Get all messages in a session
   * Sorted (created_at ascending)
   * @returns any
   * @throws ApiError
   */
  public getHistory({
    sessionId,
    limit = 100,
    offset,
  }: {
    sessionId: string;
    limit?: number;
    offset?: number;
  }): CancelablePromise<{
    items?: Array<ChatMLMessage>;
  }> {
    return this.httpRequest.request({
      method: "GET",
      url: "/sessions/{session_id}/history",
      path: {
        session_id: sessionId,
      },
      query: {
        limit: limit,
        offset: offset,
      },
    });
  }
  /**
   * Delete session history (does NOT delete related memories)
   * @returns ResourceDeletedResponse
   * @throws ApiError
   */
  public deleteSessionHistory({
    sessionId,
  }: {
    sessionId: string;
  }): CancelablePromise<ResourceDeletedResponse> {
    return this.httpRequest.request({
      method: "DELETE",
      url: "/sessions/{session_id}/history",
      path: {
        session_id: sessionId,
      },
    });
  }
  /**
   * Interact with the session
   * @returns ChatResponse
   * @throws ApiError
   */
  public chat({
    sessionId,
    accept = "application/json",
    requestBody,
  }: {
    sessionId: string;
    accept?: "application/json" | "text/event-stream";
    requestBody?: ChatInput;
  }): CancelablePromise<ChatResponse> {
    return this.httpRequest.request({
      method: "POST",
      url: "/sessions/{session_id}/chat",
      path: {
        session_id: sessionId,
      },
      headers: {
        Accept: accept,
      },
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Get memories of the agent
   * Sorted (created_at descending)
   * @returns any
   * @throws ApiError
   */
  public getAgentMemories({
    agentId,
    query,
    userId,
    limit,
    offset,
  }: {
    agentId: string;
    query: string;
    userId?: string;
    limit?: number;
    offset?: number;
  }): CancelablePromise<{
    items?: Array<Memory>;
  }> {
    return this.httpRequest.request({
      method: "GET",
      url: "/agents/{agent_id}/memories",
      path: {
        agent_id: agentId,
      },
      query: {
        query: query,
        user_id: userId,
        limit: limit,
        offset: offset,
      },
    });
  }
  /**
   * Get details of the user
   * @returns User
   * @throws ApiError
   */
  public getUser({ userId }: { userId: string }): CancelablePromise<User> {
    return this.httpRequest.request({
      method: "GET",
      url: "/users/{user_id}",
      path: {
        user_id: userId,
      },
    });
  }
  /**
   * Delete user
   * @returns ResourceDeletedResponse
   * @throws ApiError
   */
  public deleteUser({
    userId,
  }: {
    userId: string;
  }): CancelablePromise<ResourceDeletedResponse> {
    return this.httpRequest.request({
      method: "DELETE",
      url: "/users/{user_id}",
      path: {
        user_id: userId,
      },
    });
  }
  /**
   * Update user parameters
   * @returns ResourceUpdatedResponse
   * @throws ApiError
   */
  public updateUser({
    userId,
    requestBody,
  }: {
    userId: string;
    requestBody?: UpdateUserRequest;
  }): CancelablePromise<ResourceUpdatedResponse> {
    return this.httpRequest.request({
      method: "PUT",
      url: "/users/{user_id}",
      path: {
        user_id: userId,
      },
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Patch User parameters (merge instead of replace)
   * @returns ResourceUpdatedResponse
   * @throws ApiError
   */
  public patchUser({
    userId,
    requestBody,
  }: {
    userId: string;
    requestBody?: PatchUserRequest;
  }): CancelablePromise<ResourceUpdatedResponse> {
    return this.httpRequest.request({
      method: "PATCH",
      url: "/users/{user_id}",
      path: {
        user_id: userId,
      },
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Get details of the agent
   * @returns Agent
   * @throws ApiError
   */
  public getAgent({ agentId }: { agentId: string }): CancelablePromise<Agent> {
    return this.httpRequest.request({
      method: "GET",
      url: "/agents/{agent_id}",
      path: {
        agent_id: agentId,
      },
    });
  }
  /**
   * Delete agent
   * @returns ResourceDeletedResponse
   * @throws ApiError
   */
  public deleteAgent({
    agentId,
  }: {
    agentId: string;
  }): CancelablePromise<ResourceDeletedResponse> {
    return this.httpRequest.request({
      method: "DELETE",
      url: "/agents/{agent_id}",
      path: {
        agent_id: agentId,
      },
    });
  }
  /**
   * Update agent parameters
   * @returns ResourceUpdatedResponse
   * @throws ApiError
   */
  public updateAgent({
    agentId,
    requestBody,
  }: {
    agentId: string;
    requestBody?: UpdateAgentRequest;
  }): CancelablePromise<ResourceUpdatedResponse> {
    return this.httpRequest.request({
      method: "PUT",
      url: "/agents/{agent_id}",
      path: {
        agent_id: agentId,
      },
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Patch Agent parameters (merge instead of replace)
   * @returns ResourceUpdatedResponse
   * @throws ApiError
   */
  public patchAgent({
    agentId,
    requestBody,
  }: {
    agentId: string;
    requestBody?: PatchAgentRequest;
  }): CancelablePromise<ResourceUpdatedResponse> {
    return this.httpRequest.request({
      method: "PATCH",
      url: "/agents/{agent_id}",
      path: {
        agent_id: agentId,
      },
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Get docs of the agent
   * Sorted (created_at descending)
   * @returns any
   * @throws ApiError
   */
  public getAgentDocs({
    agentId,
    limit,
    offset,
    metadataFilter = "{}",
    sortBy = "created_at",
    order = "desc",
    requestBody,
  }: {
    agentId: string;
    limit?: number;
    offset?: number;
    /**
     * JSON object that should be used to filter objects by metadata
     */
    metadataFilter?: string;
    /**
     * Which field to sort by: `created_at` or `updated_at`
     */
    sortBy?: "created_at" | "updated_at";
    /**
     * Which order should the sort be: `asc` (ascending) or `desc` (descending)
     */
    order?: "asc" | "desc";
    requestBody?: any;
  }): CancelablePromise<{
    items?: Array<Doc>;
  }> {
    return this.httpRequest.request({
      method: "GET",
      url: "/agents/{agent_id}/docs",
      path: {
        agent_id: agentId,
      },
      query: {
        limit: limit,
        offset: offset,
        metadata_filter: metadataFilter,
        sort_by: sortBy,
        order: order,
      },
      body: requestBody,
    });
  }
  /**
   * Create doc of the agent
   * @returns ResourceCreatedResponse
   * @throws ApiError
   */
  public createAgentDoc({
    agentId,
    requestBody,
  }: {
    agentId: string;
    requestBody?: CreateDoc;
  }): CancelablePromise<ResourceCreatedResponse> {
    return this.httpRequest.request({
      method: "POST",
      url: "/agents/{agent_id}/docs",
      path: {
        agent_id: agentId,
      },
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Get docs of the user
   * Sorted (created_at descending)
   * @returns any
   * @throws ApiError
   */
  public getUserDocs({
    userId,
    limit,
    offset,
    metadataFilter = "{}",
    sortBy = "created_at",
    order = "desc",
    requestBody,
  }: {
    userId: string;
    limit?: number;
    offset?: number;
    /**
     * JSON object that should be used to filter objects by metadata
     */
    metadataFilter?: string;
    /**
     * Which field to sort by: `created_at` or `updated_at`
     */
    sortBy?: "created_at" | "updated_at";
    /**
     * Which order should the sort be: `asc` (ascending) or `desc` (descending)
     */
    order?: "asc" | "desc";
    requestBody?: any;
  }): CancelablePromise<{
    items?: Array<Doc>;
  }> {
    return this.httpRequest.request({
      method: "GET",
      url: "/users/{user_id}/docs",
      path: {
        user_id: userId,
      },
      query: {
        limit: limit,
        offset: offset,
        metadata_filter: metadataFilter,
        sort_by: sortBy,
        order: order,
      },
      body: requestBody,
    });
  }
  /**
   * Create doc of the user
   * @returns ResourceCreatedResponse
   * @throws ApiError
   */
  public createUserDoc({
    userId,
    requestBody,
  }: {
    userId: string;
    requestBody?: CreateDoc;
  }): CancelablePromise<ResourceCreatedResponse> {
    return this.httpRequest.request({
      method: "POST",
      url: "/users/{user_id}/docs",
      path: {
        user_id: userId,
      },
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Delete doc by id
   * @returns ResourceDeletedResponse
   * @throws ApiError
   */
  public deleteUserDoc({
    userId,
    docId,
  }: {
    userId: string;
    docId: string;
  }): CancelablePromise<ResourceDeletedResponse> {
    return this.httpRequest.request({
      method: "DELETE",
      url: "/users/{user_id}/docs/{doc_id}",
      path: {
        user_id: userId,
        doc_id: docId,
      },
    });
  }
  /**
   * Delete doc by id
   * @returns ResourceDeletedResponse
   * @throws ApiError
   */
  public deleteAgentDoc({
    agentId,
    docId,
  }: {
    agentId: string;
    docId: string;
  }): CancelablePromise<ResourceDeletedResponse> {
    return this.httpRequest.request({
      method: "DELETE",
      url: "/agents/{agent_id}/docs/{doc_id}",
      path: {
        agent_id: agentId,
        doc_id: docId,
      },
    });
  }
  /**
   * Delete memory of the agent by id
   * @returns ResourceDeletedResponse
   * @throws ApiError
   */
  public deleteAgentMemory({
    agentId,
    memoryId,
  }: {
    agentId: string;
    memoryId: string;
  }): CancelablePromise<ResourceDeletedResponse> {
    return this.httpRequest.request({
      method: "DELETE",
      url: "/agents/{agent_id}/memories/{memory_id}",
      path: {
        agent_id: agentId,
        memory_id: memoryId,
      },
    });
  }
  /**
   * Get tools of the agent
   * Sorted (created_at descending)
   * @returns any
   * @throws ApiError
   */
  public getAgentTools({
    agentId,
    limit,
    offset,
    requestBody,
  }: {
    agentId: string;
    limit?: number;
    offset?: number;
    requestBody?: any;
  }): CancelablePromise<{
    items?: Array<Tool>;
  }> {
    return this.httpRequest.request({
      method: "GET",
      url: "/agents/{agent_id}/tools",
      path: {
        agent_id: agentId,
      },
      query: {
        limit: limit,
        offset: offset,
      },
      body: requestBody,
    });
  }
  /**
   * Create tool for the agent
   * @returns ResourceCreatedResponse
   * @throws ApiError
   */
  public createAgentTool({
    agentId,
    requestBody,
  }: {
    agentId: string;
    requestBody?: CreateToolRequest;
  }): CancelablePromise<ResourceCreatedResponse> {
    return this.httpRequest.request({
      method: "POST",
      url: "/agents/{agent_id}/tools",
      path: {
        agent_id: agentId,
      },
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Delete tool by id
   * @returns ResourceDeletedResponse
   * @throws ApiError
   */
  public deleteAgentTool({
    agentId,
    toolId,
  }: {
    agentId: string;
    toolId: string;
  }): CancelablePromise<ResourceDeletedResponse> {
    return this.httpRequest.request({
      method: "DELETE",
      url: "/agents/{agent_id}/tools/{tool_id}",
      path: {
        agent_id: agentId,
        tool_id: toolId,
      },
    });
  }
  /**
   * Update agent tool definition
   * @returns ResourceUpdatedResponse
   * @throws ApiError
   */
  public updateAgentTool({
    agentId,
    toolId,
    requestBody,
  }: {
    agentId: string;
    toolId: string;
    requestBody?: UpdateToolRequest;
  }): CancelablePromise<ResourceUpdatedResponse> {
    return this.httpRequest.request({
      method: "PUT",
      url: "/agents/{agent_id}/tools/{tool_id}",
      path: {
        agent_id: agentId,
        tool_id: toolId,
      },
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Patch Agent tool parameters (merge instead of replace)
   * @returns ResourceUpdatedResponse
   * @throws ApiError
   */
  public patchAgentTool({
    agentId,
    toolId,
    requestBody,
  }: {
    agentId: string;
    toolId: string;
    requestBody?: PatchToolRequest;
  }): CancelablePromise<ResourceUpdatedResponse> {
    return this.httpRequest.request({
      method: "PATCH",
      url: "/agents/{agent_id}/tools/{tool_id}",
      path: {
        agent_id: agentId,
        tool_id: toolId,
      },
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Get status of the job
   * @returns JobStatus
   * @throws ApiError
   */
  public getJobStatus({
    jobId,
  }: {
    jobId: string;
  }): CancelablePromise<JobStatus> {
    return this.httpRequest.request({
      method: "GET",
      url: "/jobs/{job_id}",
      path: {
        job_id: jobId,
      },
    });
  }
  /**
   * Get a list of tasks
   * @returns Task
   * @throws ApiError
   */
  public listTasks(): CancelablePromise<Array<Task>> {
    return this.httpRequest.request({
      method: "GET",
      url: "/tasks",
    });
  }
  /**
   * Create a Task
   * @returns ResourceCreatedResponse
   * @throws ApiError
   */
  public createTask({
    requestBody,
  }: {
    requestBody?: CreateTask;
  }): CancelablePromise<ResourceCreatedResponse> {
    return this.httpRequest.request({
      method: "POST",
      url: "/tasks",
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Create (or start) an execution of a Task
   * @returns ResourceCreatedResponse
   * @throws ApiError
   */
  public startTaskExecution({
    taskId,
    requestBody,
  }: {
    taskId: string;
    requestBody?: CreateExecution;
  }): CancelablePromise<ResourceCreatedResponse> {
    return this.httpRequest.request({
      method: "POST",
      url: "/tasks/{task_id}/execution",
      path: {
        task_id: taskId,
      },
      body: requestBody,
      mediaType: "application/json",
    });
  }
  /**
   * Get execution (status) of a Task
   * @returns Execution
   * @throws ApiError
   */
  public getTaskExecution({
    taskId,
  }: {
    taskId: string;
  }): CancelablePromise<Execution> {
    return this.httpRequest.request({
      method: "GET",
      url: "/tasks/{task_id}/execution",
      path: {
        task_id: taskId,
      },
    });
  }
  /**
   * Get a Task by ID
   * @returns Execution
   * @throws ApiError
   */
  public getTask({ taskId }: { taskId: string }): CancelablePromise<Execution> {
    return this.httpRequest.request({
      method: "GET",
      url: "/tasks/{task_id}",
      path: {
        task_id: taskId,
      },
    });
  }
  /**
   * @returns ExecutionTransition
   * @throws ApiError
   */
  public getExecutionTransition({
    executionId,
    transitionId,
  }: {
    executionId: string;
    transitionId: string;
  }): CancelablePromise<Array<ExecutionTransition>> {
    return this.httpRequest.request({
      method: "GET",
      url: "/execution/{execution_id}/transition/{transition_id}",
      path: {
        execution_id: executionId,
        transition_id: transitionId,
      },
    });
  }
  /**
   * @returns ResourceUpdatedResponse
   * @throws ApiError
   */
  public resumeToolExecution({
    executionId,
    transitionId,
    requestBody,
  }: {
    executionId: string;
    transitionId: string;
    requestBody?: {
      responses: Array<ToolResponse>;
    };
  }): CancelablePromise<ResourceUpdatedResponse> {
    return this.httpRequest.request({
      method: "PUT",
      url: "/execution/{execution_id}/transition/{transition_id}",
      path: {
        execution_id: executionId,
        transition_id: transitionId,
      },
      body: requestBody,
      mediaType: "application/json",
    });
  }
}
