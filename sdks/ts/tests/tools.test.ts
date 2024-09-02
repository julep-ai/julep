// tests/tools.test.ts

import { afterAll, beforeAll, describe, expect, it, test } from "@jest/globals";

import { setupClient } from "./fixtures"; // Adjust the path as necessary
import { Client } from "../src";
import {
  Agents_Agent as Agent,
  Tools_Tool as Tool,
  Tools_ToolType,
} from "../src/api";

describe("Tools API", () => {
  let client: Client;
  let testAgent: Partial<Agent> & { id: string };
  let testTool: Tool;

  const mockTool = {
    description: "test description",
    name: "test name",
    parameters: { test_arg: "test val" },
    about: "about tool",
    model: "model1",
    instructions: [],
  };

  const mockToolUpdate = {
    type: "function" as Tools_ToolType,
    description: "changed description",
    name: "changed name",
    parameters: { test_arg: "test val" },
  };

  beforeAll(async () => {
    client = setupClient();
    testAgent = await client.agents.create({
      requestBody: {
        name: "test agent",
        about: "test agent about",
        instructions: ["test agent instructions"],
        default_settings: { temperature: 0.5 },
        model: "model1",
      },
    });
  });

  afterAll(async () => {
    await client.agents.delete({ id: testAgent.id });
  });

  it("tools.create", async () => {
    const response = await client.agents.createTool({
      id: testAgent.id,
      requestBody: mockTool,
    });

    expect(response).toHaveProperty("created_at");
    expect(response).toHaveProperty("id");
    expect(response).toHaveProperty("jobs");
  });

  it("tools.update", async () => {
    const response = await client.agents.updateTool({
      id: testAgent.id,
      childId: testTool.id,
      requestBody: mockToolUpdate,
    });

    expect(response).toHaveProperty("updated_at");
    expect(response).toHaveProperty("id");
    expect(response).toHaveProperty("jobs");
  });

  it("tools.list", async () => {
    const response = await client.agents.listTools({
      id: testAgent.id,
      offset: 0,
    });
    expect(response.results.length).toBeGreaterThan(0);
    const tool = response.results.find((tool) => tool.id === testTool.id);

    expect(tool).toBeDefined();
    expect(tool!.id).toBe(testTool.id);
  });

  test("tools.delete", async () => {
    const response = await client.agents.deleteTool({
      id: testAgent.id,
      childId: testTool.id,
    });

    expect(response).toBeUndefined();
  });
});
