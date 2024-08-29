import {
  Common_limit,
  Common_offset,
  Common_uuid,
  Executions_CreateExecutionRequest,
  Tasks_CreateTaskRequest,
  Tasks_PatchTaskRequest,
  Tasks_UpdateTaskRequest,
} from "./api";
import { BaseRoutes } from "./baseRoutes";

export class TasksRoutes extends BaseRoutes {
  async create({
    id,
    requestBody,
  }: {
    id: Common_uuid;
    requestBody: Tasks_CreateTaskRequest;
  }) {
    return await this.apiClient.default.tasksRouteCreate({ id, requestBody });
  }

  async createOrUpdate({
    parentId,
    id,
    requestBody,
  }: {
    parentId: Common_uuid;
    id: Common_uuid;
    requestBody: Tasks_CreateTaskRequest;
  }) {
    return await this.apiClient.default.tasksCreateOrUpdateRouteCreateOrUpdate({
      parentId,
      id,
      requestBody,
    });
  }

  async delete({ id, childId }: { id: Common_uuid; childId: Common_uuid }) {
    return await this.apiClient.default.tasksRouteDelete({ id, childId });
  }

  async list({
    id,
    limit = 100,
    offset,
    sortBy = "created_at",
    direction = "asc",
    metadataFilter = "{}",
  }: {
    id: Common_uuid;
    limit?: Common_limit;
    offset: Common_offset;
    sortBy?: "created_at" | "updated_at";
    direction?: "asc" | "desc";
    metadataFilter?: string;
  }) {
    return await this.apiClient.default.tasksRouteList({
      id,
      limit,
      offset,
      sortBy,
      direction,
      metadataFilter,
    });
  }

  async patch({
    id,
    childId,
    requestBody,
  }: {
    id: Common_uuid;
    childId: Common_uuid;
    requestBody: Tasks_PatchTaskRequest;
  }) {
    return await this.apiClient.default.tasksRoutePatch({
      id,
      childId,
      requestBody,
    });
  }

  async update({
    id,
    childId,
    requestBody,
  }: {
    id: Common_uuid;
    childId: Common_uuid;
    requestBody: Tasks_UpdateTaskRequest;
  }) {
    return await this.apiClient.default.tasksRouteUpdate({
      id,
      childId,
      requestBody,
    });
  }

  async createExecution({
    id,
    requestBody,
  }: {
    id: Common_uuid;
    requestBody: Executions_CreateExecutionRequest;
  }) {
    return await this.apiClient.default.taskExecutionsRouteCreate({
      id,
      requestBody,
    });
  }

  async listExecutions({
    id,
    limit = 100,
    offset,
    sortBy = "created_at",
    direction = "asc",
    metadataFilter = "{}",
  }: {
    id: Common_uuid;
    limit?: Common_limit;
    offset: Common_offset;
    sortBy?: "created_at" | "updated_at";
    direction?: "asc" | "desc";
    metadataFilter?: string;
  }) {
    return await this.apiClient.default.taskExecutionsRouteList({
      id,
      limit,
      offset,
      sortBy,
      direction,
      metadataFilter,
    });
  }
}
