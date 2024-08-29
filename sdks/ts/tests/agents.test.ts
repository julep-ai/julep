// agents.test.ts

import { describe, expect, test } from "@jest/globals";
import { Agents_Agent as Agent } from "../src/api";

import { setupClient } from "./fixtures";

const client = setupClient();

const mockAgent = {
  name: "test agent",
  about: "test agent about",
  instructions: ["test agent instructions"],
  default_settings: { temperature: 0.5 },
  model: "model1",
};

const mockAgentUpdate = {
  name: "updated agent",
  about: "updated agent about",
  instructions: ["updated agent instructions"],
  default_settings: { temperature: 0.5 },
  model: "model1",
};

describe("Julep Client Tests", () => {
  let testAgent: Partial<Agent> & { id: string };

  test("agents.create", async () => {
    const response = await client.agents.create({
      requestBody: mockAgent,
    });

    testAgent = response;

    expect(response).toHaveProperty("created_at");
    expect(response).toHaveProperty("jobs");
    expect(response).toHaveProperty("id");
    expect(response.id).toBe(testAgent.id);
  });

  test("agents.get", async () => {
    const response = await client.agents.get({ id: testAgent.id });

    expect(response).toHaveProperty("created_at");
    expect(response).toHaveProperty("updated_at");
    expect(response.about).toBe(mockAgent.about);
    expect(response.name).toBe(mockAgent.name);
  });

  test("agents.update", async () => {
    const response = await client.agents.update({
      id: testAgent.id,
      requestBody: mockAgentUpdate,
    });

    expect(response.id).toBe(testAgent.id);
    expect(response).toHaveProperty("updated_at");
    expect(response).toHaveProperty("jobs");
  });

  test("agents.list", async () => {
    const response = await client.agents.list({ offset: 0 });

    expect(response.items.length).toBeGreaterThan(0);

    const agent = response.items.find((agent) => agent.id === testAgent.id);

    expect(agent).toBeDefined();
    expect(agent!.id).toBe(testAgent.id);
    expect(agent).toHaveProperty("created_at");
    expect(agent).toHaveProperty("updated_at");
    expect(agent!.name).toBe(mockAgentUpdate.name);
    expect(agent!.about).toBe(mockAgentUpdate.about);
  });

  test("agents.delete", async () => {
    const response = await client.agents.delete({ id: testAgent.id });
    expect(response).toBeUndefined();
  });
});
