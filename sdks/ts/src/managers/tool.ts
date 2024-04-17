import {
  Tool,
  UpdateToolRequest,
  ResourceCreatedResponse,
  FunctionDef,
} from "../api"; // Import necessary types from your project

import { BaseManager } from "./base";

export class ToolsManager extends BaseManager {
  async list(
    agentId: string,
    {
      limit = 10,
      offset = 0,
    }: {
      limit?: number;
      offset?: number;
    } = {},
  ): Promise<Array<Tool>> {
    const result = await this.apiClient.default.getAgentTools({
      agentId,
      limit,
      offset,
    });

    return result.items || [];
  }

  async create({
    agentId,
    tool,
  }: {
    agentId: string;
    tool: {
      type: "function" | "webhook";
      function: FunctionDef;
    };
  }): Promise<Tool> {
    const result: ResourceCreatedResponse =
      await this.apiClient.default.createAgentTool({
        agentId,
        requestBody: tool,
      });

    const newTool: Tool = { ...result, ...tool };

    return newTool;
  }

  async update(
    {
      agentId,
      toolId,
      tool,
    }: {
      agentId: string;
      toolId: string;
      tool: UpdateToolRequest;
    },
    overwrite = false,
  ): Promise<Tool> {
    if (overwrite) {
      const result = await this.apiClient.default.updateAgentTool({
        agentId,
        toolId,
        requestBody: tool,
      });
      const updatedTool: Tool = { type: "function", ...result, ...tool };
      return updatedTool;
    } else {
      const result = await this.apiClient.default.patchAgentTool({
        agentId,
        toolId,
        requestBody: tool,
      });
      const updatedTool: Tool = { type: "function", ...result, ...tool };
      return updatedTool;
    }
  }

  async delete({
    agentId,
    toolId,
  }: {
    agentId: string;
    toolId: string;
  }): Promise<void> {
    await this.apiClient.default.deleteAgentTool({ agentId, toolId });
  }
}
