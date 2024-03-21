// memories.test.ts

import { describe, expect, it } from "@jest/globals";

// import { setupClient } from "./fixtures";
// import { Client } from "../src";
// import { Agent, User } from "../src/api";

describe("Julep Client Tests", () => {
  // TODO: report api not implemented
  //   let client: Client;
  //   let testAgent: Partial<Agent> & { id: string };
  //   let testUser: User;
  //   const mockAgent = {
  //     name: "test agent",
  //     about: "test agent about",
  //     instructions: [{ content: "test agent instructions" }],
  //     default_settings: { temperature: 0.5 },
  //   };
  //   const mockUser = {
  //     name: "test user",
  //     about: "test user about",
  //   };
  //   beforeEach(async () => {
  //     client = setupClient();
  //     testAgent = await client.agents.create(mockAgent);
  //     testUser = await client.users.create(mockUser);
  //   });
  //   test("async memories.list", async () => {
  //     try {
  //       const response = await client.memories.list({
  //         agentId: testAgent.id,
  //         userId: testUser.id,
  //         query: "test query",
  //         types: ["test types"],
  //         limit: 100,
  //         offset: 0,
  //       });
  //       console.error(response);
  //       expect(response.length).toBeGreaterThan(0);
  //       expect(response[0]).toHaveProperty("createdAt");
  //     } catch (error) {
  //       console.error(error);
  //     }
  //   });
  it("should pass", () => {
    expect(true).toBe(true);
  });
});
