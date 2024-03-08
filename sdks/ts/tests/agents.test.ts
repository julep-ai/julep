// agents.test.ts

import { v4 as uuidv4 } from "uuid";
import { describe, expect, test } from "@jest/globals";

import { setupClient } from "./fixtures";

const client = setupClient();

describe("Julep Client Tests", () => {
  test("agents.get", async () => {
    const response = await client.agents.get(uuidv4());

    expect(response).toHaveProperty("createdAt");
  });

  test("agents.create", async () => {
    const response = await client.agents.create({
      name: "test agent",
      about: "test agent about",
      instructions: ["test agent instructions"],
      defaultSettings: { temperature: 0.5 },
    });

    expect(response).toHaveProperty("createdAt");
  });

  test("agents.list", async () => {
    const response = await client.agents.list();

    expect(response.length).toBeGreaterThan(0);
    expect(response[0]).toHaveProperty("createdAt");
  });

  test("agents.update", async () => {
    const agentId = uuidv4();

    const response = await client.agents.update(agentId, {
      name: "test user",
      about: "test user about",
      instructions: ["test agent instructions"],
      defaultSettings: { temperature: 0.5 },
      model: "some model",
    });

    expect(response).toHaveProperty("updatedAt");
  });

  test("agents.delete", async () => {
    const response = await client.agents.delete(uuidv4());
    expect(response).toBeNull();
  });
});
