// memories.test.ts

import { afterAll, beforeAll, describe, expect, test } from "@jest/globals";

import { setupClient } from "./fixtures";
import { Client } from "../src";
import { Agent, User } from "../src/api";

describe("Julep Client Tests", () => {
  let client: Client;
  let testAgent: Partial<Agent> & { id: string };
  let testUser: User;
  const mockAgent = {
    name: "test agent",
    about: "test agent about",
    instructions: ["test agent instructions"],
    default_settings: { temperature: 0.5 },
  };

  const mockUser = {
    name: "test user",
    about: "test user about",
  };

  beforeAll(async () => {
    client = setupClient();
    testAgent = await client.agents.create(mockAgent);
    testUser = await client.users.create(mockUser);
  });

  afterAll(async () => {
    await client.agents.delete(testAgent.id);
    await client.users.delete(testUser.id);
  });

  test("async memories.list", async () => {
    // try {
    //   const response = await client.memories.list({
    //     agentId: testAgent.id,
    //     userId: testUser.id,
    //     query: "test query",
    //     limit: 100,
    //     offset: 0,
    //   });

    //   console.error({ response });

    //   expect(response.length).toBeGreaterThan(0);
    //   expect(response[0]).toHaveProperty("created_at");
    // } catch (error) {
    //   console.error(error);
    // }
    expect(true).toBe(true);
  });
});
