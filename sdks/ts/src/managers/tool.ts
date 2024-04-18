// ToolsManager class manages tool-related operations such as listing, creating, updating, and deleting tools.
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
    // Lists tools associated with a given agent. Allows pagination through `limit` and `offset` parameters.
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
    // Creates a new tool for the specified agent. The `tool` parameter must include the tool type and function definition.
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
    // Updates an existing tool. If `overwrite` is true, it replaces the existing tool with the new one; otherwise, it patches the tool with the provided changes.
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
    // Deletes a specified tool from an agent.
    await this.apiClient.default.deleteAgentTool({ agentId, toolId });
  }
}
