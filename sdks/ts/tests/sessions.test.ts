// sessions.test.ts
import { v4 as uuidv4 } from "uuid";
import { beforeAll, describe, expect, it } from "@jest/globals";

import { setupClient } from "./fixtures"; // Adjust path if necessary

describe("Sessions API", () => {
  let client: any;

  beforeAll(() => {
    client = setupClient();
  });

  it("sessions.get", async () => {
    const response = await client.sessions.get(uuidv4());

    expect(response).toHaveProperty("createdAt");
  });

  it("sessions.create", async () => {
    const response = await client.sessions.create({
      userId: uuidv4(),
      agentId: uuidv4(),
      situation: "test situation",
    });

    expect(response.createdAt).toBeDefined();
  });

  it("sessions.list", async () => {
    const response = await client.sessions.list();

    expect(response.length).toBeGreaterThan(0);
  });

  it("sessions.update", async () => {
    const response = await client.sessions.update(uuidv4(), {
      situation: "test situation",
    });

    expect(response.updatedAt).toBeDefined();
  });

  it("sessions.delete", async () => {
    const response = await client.sessions.delete(uuidv4());
    expect(response).toBeUndefined();
  });

  it("sessions.chat", async () => {
    const response = await client.sessions.chat(uuidv4().toString(), {
      messages: [
        {
          role: "user",
          content: "test content",
          name: "test name",
        },
      ],
      tools: [
        {
          type: "function",
          function: {
            description: "test description",
            name: "test name",
            parameters: { testArg: "test val" },
          },
          id: uuidv4().toString(),
        },
      ],
      toolChoice: "auto",
      frequencyPenalty: 0.5,
      lengthPenalty: 0.5,
      maxTokens: 120,
      presencePenalty: 0.5,
      repetitionPenalty: 0.5,
      seed: 1,
      stop: ["<"],
      stream: false,
      temperature: 0.7,
      topP: 0.9,
      recall: false,
      remember: false,
    });

    expect(response.response).toBeDefined();
  });

  it("sessions.suggestions", async () => {
    const response = await client.sessions.suggestions(uuidv4(), {
      limit: 10,
      offset: 10,
    });

    expect(response.length).toBeGreaterThan(0);
  });

  it("sessions.history", async () => {
    const response = await client.sessions.history(uuidv4(), {
      limit: 10,
      offset: 10,
    });

    expect(response.length).toBeGreaterThan(0);
  });
});
