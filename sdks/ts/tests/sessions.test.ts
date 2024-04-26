// sessions.test.ts
import { afterAll, beforeAll, describe, expect, it } from "@jest/globals";

import { setupClient } from "./fixtures"; // Adjust path if necessary
import { Agent, User } from "../src/api";
import { Client } from "../src";

const { TEST_MODEL } = process.env;

const model: string = TEST_MODEL || "julep-ai/samantha-1-turbo";

const mockAgent = {
  model,
  name: "test agent",
  about: "test agent about",
  instructions: ["test agent instructions"],
  default_settings: { temperature: 0.5 },
};

const mockUser = {
  name: "test user",
  about: "test user about",
};

const mockSession = {
  situation: "test situation",
};

const mockSessionUpdate = {
  situation: "updated situation",
};

describe("Sessions API", () => {
  let client: Client;
  let testSessionId: string;
  let testUser: User;
  let testAgent: Partial<Agent> & { id: string };

  beforeAll(async () => {
    client = setupClient();
    testAgent = await client.agents.create(mockAgent);
    testUser = await client.users.create(mockUser);
  });

  afterAll(async () => {
    await client.agents.delete(testAgent.id);
    await client.users.delete(testUser.id);
  });

  it("sessions.create", async () => {
    const response = await client.sessions.create({
      userId: testUser.id,
      agentId: testAgent.id,
      ...mockSession,
    });

    testSessionId = response.id;

    expect(response).toBeDefined();
    expect(response).toHaveProperty("created_at");
  });

  it("sessions.get", async () => {
    const response = await client.sessions.get(testSessionId);

    expect(response).toHaveProperty("created_at");
    expect(response.situation).toBe(mockSession.situation);
  });

  it("sessions.update", async () => {
    const response = await client.sessions.update(
      testSessionId,
      mockSessionUpdate,
    );

    expect(response).toHaveProperty("updated_at");
  });

  it("sessions.update with overwrite", async () => {
    const response = await client.sessions.update(
      testSessionId,
      mockSessionUpdate,
      true,
    );

    expect(response).toHaveProperty("updated_at");
  });

  it("sessions.list", async () => {
    const response = await client.sessions.list();

    expect(response.length).toBeGreaterThan(0);

    const session = response.find((session) => session.id === testSessionId);

    expect(session?.situation).toBe(mockSessionUpdate.situation);
  });

  it("sessions.chat", async () => {
    try {
      const response = await client.sessions.chat(testSessionId, {
        messages: [
          {
            role: "user",
            content: "test content",
            name: "test name",
          },
        ],
        max_tokens: 1000,
        presence_penalty: 0.5,
        repetition_penalty: 0.5,
        temperature: 0.7,
        top_p: 0.9,
      });

      expect(response.response).toBeDefined();
    } catch (error) {
      console.error("error", error);
    }
  }, 5000);

  //   it("sessions.suggestions", async () => {
  //     const response = await client.sessions.suggestions(testSessionId);

  //     expect(response.length).toBeGreaterThan(0);
  //   });

  it("sessions.history", async () => {
    const response = await client.sessions.history(testSessionId);

    expect(response.length).toBeGreaterThan(0);
  });

  it("sessions.deleteHistory", async () => {
    const response = await client.sessions.deleteHistory(testSessionId);

    expect(response).toBeUndefined();
  });

  it("sessions.delete", async () => {
    const response = await client.sessions.delete(testSessionId);
    expect(response).toBeUndefined();
  });
});
