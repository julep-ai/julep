// tests/tools.test.ts

import { afterAll, beforeAll, describe, expect, it, test } from "@jest/globals";

import { setupClient } from "./fixtures"; // Adjust the path as necessary
import { Client } from "../src";
import { Agent, Tool } from "../src/api";

describe("Tools API", () => {
  let client: Client;
  let testAgent: Partial<Agent> & { id: string };
  let testTool: Tool;

  const mockTool = {
    function: {
      description: "test description",
      name: "test name",
      parameters: { test_arg: "test val" },
    },
  };

  const mockToolUpdate = {
    function: {
      description: "changed description",
      name: "changed name",
      parameters: { test_arg: "test val" },
    },
  };

  beforeAll(async () => {
    client = setupClient();
    testAgent = await client.agents.create({
      name: "test agent",
      about: "test agent about",
      instructions: ["test agent instructions"],
      default_settings: { temperature: 0.5 },
    });
  });

  afterAll(async () => {
    await client.agents.delete(testAgent.id);
  });

  it("tools.create", async () => {
    const response = await client.tools.create({
      agentId: testAgent.id,
      tool: {
        type: "function",
        ...mockTool,
      },
    });

    testTool = response;

    expect(response).toHaveProperty("created_at");
    expect(response.function.description).toBe(mockTool.function.description);
    expect(response.function.name).toBe(mockTool.function.name);
  });

  it("tools.update", async () => {
    const response = await client.tools.update({
      agentId: testAgent.id,
      toolId: testTool.id,
      tool: mockToolUpdate,
    });

    expect(response).toHaveProperty("updated_at");
    expect(response.function.description).toBe(
      mockToolUpdate.function.description,
    );
    expect(response.function.name).toBe(mockToolUpdate.function.name);
  });

  it("tools.list", async () => {
    const response = await client.tools.list(testAgent.id);
    expect(response.length).toBeGreaterThan(0);
    const tool = response.find((tool) => tool.id === testTool.id);

    expect(tool).toBeDefined();
    expect(tool!.id).toBe(testTool.id);
    // expect(tool!.function.name).toBe(mockToolUpdate.function.name);
    // expect(tool!.function.description).toBe(
    //   mockToolUpdate.function.description,
    // );
  });

  test("tools.delete", async () => {
    const response = await client.tools.delete({
      agentId: testAgent.id,
      toolId: testTool.id,
    });

    expect(response).toBeUndefined();
  });
});
