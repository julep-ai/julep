import {
  Common_limit,
  Common_offset,
  Common_uuid,
  Executions_TaskTokenResumeExecutionRequest,
  Executions_UpdateExecutionRequest,
} from "./api";
import { BaseRoutes } from "./baseRoutes";

export class ExecutionsRoutes extends BaseRoutes {
  async resume({
    taskToken,
    requestBody,
  }: {
    taskToken: string;
    requestBody: Executions_TaskTokenResumeExecutionRequest;
  }) {
    return await this.apiClient.default.executionsRouteResumeWithTaskToken({
      taskToken,
      requestBody,
    });
  }

  async get({ id }: { id: Common_uuid }) {
    return await this.apiClient.default.executionsRouteGet({ id });
  }

  async update({
    id,
    requestBody,
  }: {
    id: Common_uuid;
    requestBody: Executions_UpdateExecutionRequest;
  }) {
    return await this.apiClient.default.executionsRouteUpdate({
      id,
      requestBody,
    });
  }

  async listTransitions({
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
    return await this.apiClient.default.executionTransitionsRouteList({
      id,
      limit,
      offset,
      sortBy,
      direction,
      metadataFilter,
    });
  }
}
