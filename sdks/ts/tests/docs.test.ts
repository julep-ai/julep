// docs.test.ts

import { afterAll, beforeAll, describe, expect, test } from "@jest/globals";

import { setupClient } from "./fixtures";
import { Client } from "../src";
import {
  Agents_Agent as Agent,
  Common_ResourceCreatedResponse,
} from "../src/api";

describe("Julep Client Tests", () => {
  let client: Client;
  let testAgent: Partial<Agent> & { id: string };
  let testUser: Common_ResourceCreatedResponse;
  let testAgentDocId: string;

  const mockDoc = { title: "test title", content: "test content" };

  beforeAll(async () => {
    client = setupClient();
    testAgent = await client.agents.create({
      requestBody: {
        name: "test agent",
        about: "test about",
        instructions: [],
        model: "model1",
      },
    });
    testUser = await client.users.create({
      requestBody: {
        name: "test user",
        about: "test about",
      },
    });
  });

  afterAll(async () => {
    await client.agents.delete({ id: testAgent.id });
    await client.users.delete({ id: testUser.id });
  });

  test("agent docs.create", async () => {
    const response = await client.agents.createDoc({
      id: testAgent.id,
      requestBody: mockDoc,
    });

    testAgentDocId = response.id;

    expect(response).toHaveProperty("created_at");
    expect(response).toHaveProperty("id");
    expect(response).toHaveProperty("jobs");
  });

  test("user docs.create", async () => {
    const response = await client.users.createDoc({
      id: testUser.id,
      requestBody: mockDoc,
    });

    expect(response).toHaveProperty("created_at");
    expect(response).toHaveProperty("id");
    expect(response).toHaveProperty("jobs");
  });

  test("agent list docs", async () => {
    const response = await client.agents.listDocs({
      id: testAgent.id,
      offset: 0,
    });

    expect(response.results.length).toBeGreaterThan(0);
    expect(response.results[0].content).toBe(mockDoc.content);
    expect(response.results[0].title).toBe(mockDoc.title);
  });

  test("user list docs", async () => {
    const response = await client.users.listDocs({
      id: testUser.id,
      offset: 0,
    });

    expect(response.results.length).toBeGreaterThan(0);
    expect(response.results[0].content).toBe(mockDoc.content);
    expect(response.results[0].title).toBe(mockDoc.title);
  });

  test("agent docs.delete", async () => {
    const response = await client.agents.deleteDoc({
      id: testAgent.id,
      childId: testAgentDocId,
    });

    expect(response).toBeUndefined();
  });

  test("user docs.delete", async () => {
    const response = await client.agents.deleteDoc({
      id: testUser.id,
      childId: testAgentDocId,
    });

    expect(response).toBeUndefined();
  });
});
