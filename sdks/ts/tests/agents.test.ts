// agents.test.ts

import { describe, expect, test } from "@jest/globals";
import { Agent } from "../src/api";

import { setupClient } from "./fixtures";

const client = setupClient();

const mockAgent = {
  name: "test agent",
  about: "test agent about",
  instructions: ["test agent instructions"],
  default_settings: { temperature: 0.5 },
};

const mockAgentUpdate = {
  name: "updated agent",
  about: "updated agent about",
  instructions: ["updated agent instructions"],
  default_settings: { temperature: 0.5 },
};

describe("Julep Client Tests", () => {
  let testAgent: Partial<Agent> & { id: string };

  test("agents.create", async () => {
    const response = await client.agents.create(mockAgent);

    testAgent = response;

    expect(response).toHaveProperty("created_at");
    expect(response.about).toBe(mockAgent.about);
    expect(response.name).toBe(mockAgent.name);
    expect(response.instructions).toHaveLength(1);
  });

  test("agents.get", async () => {
    const response = await client.agents.get(testAgent.id);

    expect(response).toHaveProperty("created_at");
    expect(response).toHaveProperty("updated_at");
    expect(response.about).toBe(mockAgent.about);
    expect(response.name).toBe(mockAgent.name);
    expect(response.instructions).toHaveLength(1);
  });

  test("agents.update", async () => {
    const response = await client.agents.update(testAgent.id, mockAgentUpdate);

    expect(response.id).toBe(testAgent.id);
    expect(response).toHaveProperty("updated_at");
    expect(response.name).toBe(mockAgentUpdate.name);
    expect(response.about).toBe(mockAgentUpdate.about);
  });

  test("agents.list", async () => {
    const response = await client.agents.list();

    expect(response.length).toBeGreaterThan(0);

    const agent = response.find((agent) => agent.id === testAgent.id);

    expect(agent).toBeDefined();
    expect(agent!.id).toBe(testAgent.id);
    expect(agent).toHaveProperty("created_at");
    expect(agent).toHaveProperty("updated_at");
    expect(agent!.name).toBe(mockAgentUpdate.name);
    expect(agent!.about).toBe(mockAgentUpdate.about);
  });

  test("agents.delete", async () => {
    const response = await client.agents.delete(testAgent.id);
    expect(response).toBeUndefined();
  });
});
