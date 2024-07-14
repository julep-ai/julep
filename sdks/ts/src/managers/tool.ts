import typia, { tags } from "typia";

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
    agentId: string & tags.Format<"uuid">,
    options: {
      limit?: number &
        tags.Type<"uint32"> &
        tags.Minimum<1> &
        tags.Maximum<1000>;
      offset?: number & tags.Type<"uint32"> & tags.Minimum<0>;
    } = {},
  ): Promise<Array<Tool>> {
    typia.assertGuard<string & tags.Format<"uuid">>(agentId);

    const { limit = 10, offset = 0 } = typia.assert<{
      limit?: number &
        tags.Type<"uint32"> &
        tags.Minimum<1> &
        tags.Maximum<1000>;
      offset?: number & tags.Type<"uint32"> & tags.Minimum<0>;
    }>(options);

    // Lists tools associated with a given agent. Allows pagination through `limit` and `offset` parameters.
    const result = await this.apiClient.default.getAgentTools({
      agentId,
      limit,
      offset,
    });

    return result.items || [];
  }

  async create(options: {
    agentId: string & tags.Format<"uuid">;
    tool: {
      type: "function" | "webhook";
      function: FunctionDef;
    };
  }): Promise<Tool> {
    const { agentId, tool } = typia.assert<{
      agentId: string & tags.Format<"uuid">;
      tool: {
        type: "function" | "webhook";
        function: FunctionDef;
      };
    }>(options);

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
    options: {
      agentId: string & tags.Format<"uuid">;
      toolId: string & tags.Format<"uuid">;
      tool: UpdateToolRequest;
    },
    overwrite = false,
  ): Promise<Tool> {
    const { agentId, toolId, tool } = typia.assert<{
      agentId: string & tags.Format<"uuid">;
      toolId: string & tags.Format<"uuid">;
      tool: UpdateToolRequest;
    }>(options);

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

  async delete(options: {
    agentId: string & tags.Format<"uuid">;
    toolId: string & tags.Format<"uuid">;
  }): Promise<void> {
    const { agentId, toolId } = typia.assert<{
      agentId: string & tags.Format<"uuid">;
      toolId: string & tags.Format<"uuid">;
    }>(options);

    // Deletes a specified tool from an agent.
    await this.apiClient.default.deleteAgentTool({ agentId, toolId });
  }
}
